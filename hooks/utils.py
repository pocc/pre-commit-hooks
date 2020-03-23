#!/usr/bin/env python
"""fns for clang-format, clang-tidy, oclint"""
###############################################################################
import argparse
import difflib
import shutil
import subprocess as sp
import sys


class Command:
    """Super class that all commands inherit"""

    def __init__(self, command, look_behind, args):
        self.args = args
        self.look_behind = look_behind
        self.command = command
        self.files = []
        self.edit_in_place = False

        self.stdout = ""
        self.stderr = ""
        self.returncode = 0

    def check_installed(self):
        """Check if command is installed and fail exit if not."""
        path = shutil.which(self.command)
        if path is None:
            website = "https://github.com/pocc/pre-commit-hooks#prerequisites"
            problem = self.command + " not found"
            details = """Make sure {} is installed and on your PATH.\nFor more info: {}""".format(
                self.command, website
            )  # noqa: E501
            self.raise_error(problem, details)

    def parse_args(self, args):
        """Parse the args into usable variables"""
        parser = argparse.ArgumentParser()
        parser.add_argument("filenames", nargs="*", help="Filenames to check")
        parser.add_argument("--version", nargs=1, help="Version check")
        # Exclude this filename from args
        known_args, self.args = parser.parse_known_args(args)
        if "version" in known_args and known_args.version is not None:
            expected_version = known_args.version[0]
            actual_version = self.get_version_str()
            self.assert_version(actual_version, expected_version)
        self.files = known_args.filenames

    def add_if_missing(self, new_args):
        """Add a default if it's missing from the command. This library
        exists to force checking, so prefer those options.
        len(new_args) should be 1 or 2 for options like --key value

        If arg is missing, add new_args to command's args"""
        args = []
        # Treat args with '=' as 2 args, not 1. Create two new arrays so that
        # discrepancies in '=' usage don't cause an arg to be misidentified.
        for arg in self.args:
            args += arg.split("=")
        temp_new_args = []
        for arg in new_args:
            temp_new_args += arg.split("=")

        new_args_len = len(temp_new_args)
        if new_args_len == 1:
            if temp_new_args[0] not in args:
                self.args += new_args
        else:
            for i in range(len(self.args) - new_args_len):
                if args[i : i + new_args_len] == temp_new_args:
                    return
            self.args += new_args

    def assert_version(self, actual_ver, expected_ver):
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

    def raise_error(self, problem, details):
        """Raise a formatted error."""
        format_list = [self.command, problem, details]
        self.stderr = """Problem with {}: {}\n{}\n""".format(*format_list)
        self.returncode = 1
        sys.stderr.write(self.stderr)
        sys.exit(self.returncode)

    def get_version_str(self):
        """Get the version string like 8.0.0 for a given command."""
        args = [self.command, "--version"]
        sp_child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        version_str = str(sp_child.stdout, encoding="utf-8")
        # After version like `8.0.0` is expected to be '\n' or ' '
        if self.look_behind not in version_str:
            details = """The version format for this command has changed.
Create an issue at github.com/pocc/pre-commit-hooks."""
            self.raise_error("getting version", details)
        version = version_str.split(self.look_behind)[1].split()[0]
        return version

    def run_command(self, filename):
        """Run the command and check for errors"""
        args = [self.command, filename] + self.args
        sp_child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        return sp_child


class ClangAnalyzerCmd(Command):
    """Commands that statically analyze code: clang-tidy, oclint"""

    def __init__(self, command, look_behind, args):
        super().__init__(command, look_behind, args)

    def parse_ddash_args(self):
        """pre-commit sends file as last arg, which causes problems with --
        This function converts args (1 3 5 7 -- 6 8 0) => (0 1 3 5 7 -- 6 8),
        Where 0 is the file pre-commit sends to the utility
        See https://github.com/pre-commit/pre-commit/issues/1000

        Skip this for clang-format, as it's unexpected
        Rotate if -- exists AND last arg is file AND pre-commit called $0"""
        if "--" in self.args:
            idx = self.args.index("--")
            self.args = [self.args[-1]] + self.args[:idx] + self.args[idx:-1]
        # Add a -- -DCAMKE_EXPORT_COMPILE_COMMANDS if -- is not specified
        # To avoid compilation database errors.


class FormatterCmd(Command):
    """Commands that format code: clang-format, uncrustify"""

    def __init__(self, command, look_behind, args):
        super().__init__(command, look_behind, args)
        self.file_flag = None

    @staticmethod
    def format_as_diff(lines):
        """Function to remove empty diff lines, convert to bash diff format
        Python uses +/-, so convert that to </>

        For example:
            < this is
            < expected
            ---
            > and this is actual
        """
        output = []
        left_toggle = True  # to imitate bash diff
        for line in lines:
            if line[0] == "+":
                if not left_toggle:
                    output += ["\n"]
                output += ["< " + line[1:]]
                left_toggle = True
            elif line[0] == "-":
                if left_toggle:
                    output += ["---"]
                output += ["> " + line[1:]]
                left_toggle = False
        return output

    def compare_to_formatted(self, filename):
        actual = self.get_filelines(filename)
        expected = self.get_formatted_lines(filename)
        if self.edit_in_place:
            # If edit in place is used, the formatter will fix in place with
            # no stdout. So compare the before/after file for hook pass/fail
            expected = self.get_filelines(filename)
        python_diff = list(difflib.ndiff(expected, actual))
        diff = self.format_as_diff(python_diff)
        if len(diff) > 0:
            self.stderr = "\n" + "\n".join(diff) + "\n"
            sys.stdout.write(self.stderr)
            self.returncode = 1
            sys.exit(self.returncode)

    def get_filename_opts(self, filename):
        """uncrustify, to get stdout like clang-format, requires -f flag"""
        if self.file_flag and not self.edit_in_place:
            return [self.file_flag, filename]
        return [filename]

    def get_formatted_lines(self, filename: str) -> [str]:
        filename_opts = self.get_filename_opts(filename)
        args = [self.command, *self.args, *filename_opts]
        child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        if self.command == "uncrustify" and b"Parsing:" in child.stderr:
            child.stderr = b""
        if len(child.stderr) > 0:
            problem = "Unexpected Stderr received from " + self.command
            self.raise_error(problem, str(child.stderr, encoding="utf-8"))
        lines_str = child.stdout.decode("utf-8")
        if lines_str == "":
            return []
        return lines_str.split("\n")

    @staticmethod
    def get_filelines(filename) -> [str]:
        with open(filename, "rb") as f:
            filetext = f.read()
        return str(filetext, encoding="utf-8").split("\n")
