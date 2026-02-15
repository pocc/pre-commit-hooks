#!/usr/bin/env python
"""fns for clang-format, clang-tidy, oclint"""
import difflib
import os
import re
import selectors
import shutil
import subprocess as sp
import sys
from typing import List
from typing import Optional


class Command:
    """Super class that all commands inherit"""

    def __init__(self, command: str, look_behind: str, args: List[str]):
        self.args = args
        self.look_behind = look_behind
        self.command = command
        # Will be [] if not run using pre-commit or if there are no committed files
        self.files = self.get_added_files()
        self.edit_in_place = False

        self.output = []

        self.stdout_re = None
        self.stderr_re = None
        self.returncode = 0

    def check_installed(self):
        """Check if command is installed and fail exit if not."""
        path = shutil.which(self.command)
        if path is None:
            website = "https://github.com/pocc/pre-commit-hooks#example-usage"
            problem = self.command + " not found"
            details = """Make sure {} is installed and on your PATH.\nFor more info: {}""".format(
                self.command, website
            )  # noqa: E501
            self.raise_error(problem, details)

    def get_added_files(self):
        """Find added files using git."""
        # Use self.args if available (for testing), otherwise fall back to sys.argv
        added_files = self.args[1:] if self.args else sys.argv[1:]
        # cfg files are used by uncrustify and won't be source files
        added_files = [f for f in added_files if os.path.exists(f) and not f.endswith(".cfg")]

        # Taken from https://github.com/pre-commit/pre-commit-hooks/blob/master/pre_commit_hooks/util.py
        # If no files are provided and if this is used as a command,
        # Find files the same way pre-commit does.
        if len(added_files) == 0:
            cmd = ["git", "diff", "--staged", "--name-only", "--diff-filter=A"]
            sp_child = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
            if sp_child.stderr or sp_child.returncode != 0:
                self.raise_error(
                    "Problem determining which files are being committed using git.", sp_child.stderr.decode()
                )
            added_files = sp_child.stdout.decode().splitlines()
        return added_files

    def parse_args(self, args: List[str]):
        """Parse the args into usable variables"""
        self.args = list(args[1:])  # don't include calling function
        for arg in args:
            if arg in self.files and not arg.startswith("-"):
                self.args.remove(arg)
            if arg.startswith("--version"):
                # If --version is passed in as 2 arguments, where the second is version
                if arg == "--version" and args.index(arg) != len(args) - 1:
                    expected_version = args[args.index(arg) + 1]
                # Expected split of --version=8.0.0 or --version 8.0.0 with as many spaces as needed
                else:
                    expected_version = arg.replace(" ", "").replace("=", "").replace("--version", "")
                actual_version = self.get_version_str()
                self.assert_version(actual_version, expected_version)
        # All commands other than clang-tidy or oclint require files, --version ok
        is_cmd_clang_analyzer = self.command == "clang-tidy" or self.command == "oclint"
        has_args = self.files or self.args or "version" in self.args
        if not has_args and not is_cmd_clang_analyzer:
            self.raise_error("Missing arguments", "No file arguments found and no files are pending commit.")

    def add_if_missing(self, new_args: List[str]):
        """Add a default if it's missing from the command. This library
        exists to force checking, so prefer those options.
        len(new_args) should be 1, or 2 for options like --key=value

        If first arg is missing, add new_args to command's args
        Do not change an option - in those cases return."""
        new_arg_key = new_args[0].split("=")[0]
        for arg in self.args:
            existing_arg_key = arg.split("=")[0]
            if existing_arg_key == new_arg_key:
                return
        self.args += new_args

    def assert_version(self, actual_ver: str, expected_ver: str):
        """--version hook arg enforces specific versions of tools."""
        expected_len = len(expected_ver)  # allows for fuzzy versions
        if expected_ver not in actual_ver[:expected_len]:
            problem = "Version of " + self.command + " is wrong"
            details = """Expected version: {}
Found version: {}
Edit your pre-commit config or use a different version of {}.""".format(
                expected_ver, actual_ver, self.command
            )
            self.raise_error(problem, details)
        # If the version is correct, exit normally
        sys.exit(0)

    def raise_error(self, problem: str, details: str):
        """Raise a formatted error."""
        format_list = [self.command, problem, details]
        stderr_str = """Problem with {}: {}\n{}\n""".format(*format_list)
        # All strings are generated by this program, so decode should be safe
        self.output = [('stderr', stderr_str.encode())]
        self.returncode = 1
        self.exit_on_error()

    def get_version_str(self):
        """Get the version string like 8.0.0 for a given command."""
        args = [self.command, "--version"]
        sp_child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        version_str = str(sp_child.stdout, encoding="utf-8")
        # After version like `8.0.0` is expected to be '\n' or ' '
        regex = self.look_behind + r"((?:\d+\.)+[\d+_\+\-a-z]+)"
        search = re.search(regex, version_str)
        if not search:
            details = """The version format for this command has changed.
Create an issue at github.com/pocc/pre-commit-hooks."""
            self.raise_error("getting version", details)
        version = search.group(1)
        return version


class StaticAnalyzerCmd(Command):
    """Commands that analyze code and are not formatters."""

    def __init__(self, command: str, look_behind: str, args: List[str]):
        super().__init__(command, look_behind, args)

    def run_command(self, args: List[str], input_data: Optional[str] = None, env: Optional[dict] = None):
        """Run the command and check for errors. Args includes options and filepaths"""
        args = [self.command, *args]
        run_kwargs = {
            "stdout": sp.PIPE,
            "stderr": sp.PIPE,
            "bufsize": 0,
        }
        if env is not None:
            env = {**os.environ, **env}
            run_kwargs["env"] = env
        if input_data is not None:
            run_kwargs["stdin"] = sp.PIPE

        sp_child = sp.Popen(args, **run_kwargs)

        os.set_blocking(sp_child.stdout.fileno(), False)
        os.set_blocking(sp_child.stderr.fileno(), False)
        if input_data is not None:
            os.set_blocking(sp_child.stdin.fileno(), False)

        sel = selectors.DefaultSelector()
        sel.register(sp_child.stdout, selectors.EVENT_READ, data='stdout')
        sel.register(sp_child.stderr, selectors.EVENT_READ, data='stderr')
        if input_data is not None:
            sel.register(sp_child.stdin, selectors.EVENT_WRITE, data='stdin')

        bytes_written = 0
        while True:
            if not sel.get_map():
                break
            for key, mask in sel.select():
                if key.data == 'stdin' and (mask & selectors.EVENT_WRITE):
                    if bytes_written < len(input_data):
                        count = key.fileobj.write(input_data[bytes_written:])
                        bytes_written += count
                    else:
                        sel.unregister(key.fileobj)
                        key.fileobj.close()
                elif key.data in ('stdout', 'stderr') and (mask & selectors.EVENT_READ):
                    data = key.fileobj.read()
                    if data:
                        self.output.append((key.data, data))
                    else:
                        sel.unregister(key.fileobj)
                        key.fileobj.close()
        sel.close()
        sp_child.wait()
        self.returncode = sp_child.returncode

    def exit_on_error(self):
        for to, msg in self.output:
            if to == 'stdout':
                #if self.stdout_re and not self.stdout_re.match(text):
                #    continue
                sys.stdout.buffer.write(msg)
                sys.stdout.flush()
            else:
                #if self.stderr_re and not self.stderr_re.match(text):
                #    continue
                sys.stderr.buffer.write(msg)
                sys.stderr.flush()
        sys.exit(self.returncode)

    #def exit_on_error(self):
    #    if self.returncode != 0:
    #        if self.stdout_re:
    #            filtered = sorted({line.strip() for line in self.stdout.splitlines() if self.stdout_re.match(line.strip())})
    #            if filtered:
    #                sys.stdout.buffer.write(b"\n".join(filtered) + b"\n")
    #        else:
    #            sys.stdout.buffer.write(self.stdout)
    #        if self.stderr_re:
    #            filtered = sorted({line.strip() for line in self.stderr.splitlines() if self.stderr_re.match(line.strip())})
    #            if filtered:
    #                sys.stderr.buffer.write(b"\n".join(filtered) + b"\n")
    #        else:
    #            sys.stderr.buffer.write(self.stderr)
    #        sys.exit(self.returncode)


class FormatterCmd(Command):
    """Commands that format code: clang-format, uncrustify"""

    def __init__(self, command: str, look_behind: str, args: List[str]):
        super().__init__(command, look_behind, args)
        self.file_flag = None

    def set_diff_flag(self):
        self.no_diff_flag = "--no-diff" in self.args
        if self.no_diff_flag:
            self.args.remove("--no-diff")

    def compare_to_formatted(self, filename_str: str) -> None:
        """Compare the expected formatted output to file contents."""
        # This string encode is from argparse, so we should be able to trust it.
        filename = filename_str.encode()
        actual = self.get_filelines(filename_str)
        expected = self.get_formatted_lines(filename_str)
        if self.edit_in_place:
            # If edit in place is used, the formatter will fix in place with
            # no stdout. So compare the before/after file for hook pass/fail
            expected = self.get_filelines(filename_str)
        diff = list(
            difflib.diff_bytes(difflib.unified_diff, actual, expected, fromfile=b"original", tofile=b"formatted")
        )
        if len(diff) > 0:
            if not self.no_diff_flag:
                header = filename + b"\n" + 20 * b"=" + b"\n"
                self.stderr += header + b"\n".join(diff) + b"\n"
            self.returncode = 1

    def get_filename_opts(self, filename: str):
        """uncrustify, to get stdout like clang-format, requires -f flag"""
        if self.file_flag and not self.edit_in_place:
            return [self.file_flag, filename]
        return [filename]

    def get_formatted_lines(self, filename: str) -> List[bytes]:
        """Get the expected output for a command applied to a file."""
        filename_opts = self.get_filename_opts(filename)
        args = [self.command, *self.args, *filename_opts]
        child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        if len(child.stderr) > 0 or child.returncode != 0:
            problem = f"Unexpected Stderr/return code received when analyzing {filename}.\nArgs: {args}"
            self.raise_error(problem, child.stdout.decode() + child.stderr.decode())
        if child.stdout == b"":
            return []
        return child.stdout.split(b"\x0a")

    def get_filelines(self, filename: str):
        """Get the lines in a file."""
        if not os.path.exists(filename):
            self.raise_error(f"File {filename} not found", "Check your path to the file.")
        with open(filename, "rb") as f:
            filetext = f.read()
        return filetext.split(b"\x0a")
