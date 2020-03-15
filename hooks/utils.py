#!/usr/bin/env python
"""fns for clang-format, clang-tidy, oclint"""
###############################################################################
import argparse
import shutil
import subprocess as sp
import sys


class Command:
    """Super class that all commands inherit"""

    def __init__(self, command, look_behind, args):
        self.args = args
        self.command = command
        self.version_lookbehind = look_behind
        self.files = []

        self.check_installed()

        self.retcode = 0
        self.stdout = b""
        self.stderr = b""

    def raise_error(self, problem, details):
        """Raise a formatted error."""
        msg = "Problem with {}: {}\n{}".format(self.command, problem, details)
        print(msg)
        self.stderr = msg
        self.retcode = 1

    def get_version_str(self):
        """Get the version string like 8.0.0 for a given command."""
        sp_child = sp.run([self.command, "--version"], capture_output=True)
        self.check_sp_errors(sp_child)
        version_str = str(sp_child.stdout)
        # After version like `8.0.0` is expected to be '\n' or ' '
        if self.version_lookbehind not in version_str:
            self.raise_error(
                "getting version",
                "The version format for this command has changed."
                "Create an issue at github.com/pocc/pre-commit-hooks.",
            )
        version = (
            version_str.split(self.version_lookbehind)[1]
            .split("\\n")[0]
            .split(" ")[0]
        )
        return version

    def check_installed(self):
        """Check if command is installed and fail exit if not."""
        # If result is None, then executable was not found
        path = shutil.which(self.command)
        if path is None:
            website = "https://github.com/pocc/pre-commit-hooks#prerequisites"
            problem = self.command + " not found"
            details = (
                "Make sure "
                + self.command
                + " is installed and on your PATH.\n For more info: "
                + website
            )
            self.raise_error(problem, details)

    def run_command(self, filename):
        """Run the command and check for errors"""
        sp_child = sp.run(
            [self.command, filename] + self.args, capture_output=True
        )
        self.check_sp_errors(sp_child)

    def check_sp_errors(self, sp_child):
        """Check for errors for a given executed subprocess and command."""
        sp_descriptor = "running command with args, " + " ".join(self.args)
        self.stderr = sp_child.stderr.decode("utf-8")
        self.stdout = sp_child.stdout.decode("utf-8")
        if sp_child.returncode != 0:
            self.raise_error(
                "On "
                + sp_descriptor
                + "\n\nReturn code:"
                + str(sp_child.returncode),
                "\nSTDOUT:\n"
                + sp_child.stdout.decode("utf-8")
                + "\nSTDERR:\n"
                + sp_child.stderr.decode("utf-8"),
            )
            # It's already being fromatted into stderr, so drop it here
            self.stdout = ""

    def assert_version(self, actual_version, expected_version):
        """--version hook arg enforces specific versions of tools."""
        expected_len = len(expected_version)  # allows for fuzzy versions
        if expected_version not in actual_version[:expected_len]:
            problem = "Version of " + self.command + " is wrong"
            details = (
                "Expected version is "
                + expected_version
                + " but actual system version is "
                + actual_version
                + ".\nEdit your pre-commit config or use "
                + "a different version of "
                + self.command + "."
            )
            self.raise_error(problem, details)

    def parse_args(self, args):
        """pre-commit sends file as last arg, which causes problems with --
        This function converts args (1 3 5 7 -- 6 8 0) => (0 1 3 5 7 -- 6 8),
        Where 0 is the file pre-commit sends to the utility
        See https://github.com/pre-commit/pre-commit/issues/1000

        Skip this for clang-format, as it's unexpected
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("filenames", nargs="*", help="Filenames to check")
        parser.add_argument("--version", nargs=1, help="Version check")
        known_args, other_args = parser.parse_known_args(
            args
        )  # Exclude this filename from args
        if "version" in known_args and known_args.version is not None:
            expected_version = known_args.version[0]
            actual_version = self.get_version_str()
            self.assert_version(actual_version, expected_version)

        # Rotate if -- exists AND last arg is file AND pre-commit called $0
        if "--" in other_args:
            dd_idx = args.index("--")
            other_args = (
                [other_args[-1]] + other_args[:dd_idx] + other_args[dd_idx:-1]
            )
        # Add a -- -DCAMKE_EXPORT_COMPILE_COMMANDS if -- is not specified
        # To avoid compilation database errors. Skipping clang-format
        # for arg rotation, as this may actually create errors
        elif self.command != "clang-format":
            other_args += ["--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
        self.files = known_args.filenames
        self.args = other_args

    def pipe_to_std_files(self):
        """Send stdout/stderr of this command to system stdout/stderr"""
        sys.stdout.buffer.write(self.stdout)
        sys.stderr.buffer.write(self.stderr)
