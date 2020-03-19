#!/usr/bin/env python
"""fns for clang-format, clang-tidy, oclint"""
###############################################################################
import argparse
import shutil
import subprocess as sp
import sys


class Command:
    """Super class that all commands inherit"""

    def __init__(self, command, look_behind, args, uses_ddash):
        self.args = args
        self.look_behind = look_behind
        self.command = command
        # If command requires rotation of args after -- (see parse_ddash_args)
        self.uses_ddash = uses_ddash
        self.files = []

        self.stdout = ""
        self.stderr = ""
        self.returncode = 0

    def check_installed(self):
        """Check if command is installed and fail exit if not."""
        path = shutil.which(self.command)
        if path is None:
            website = "https://github.com/pocc/pre-commit-hooks#prerequisites"
            problem = self.command + " not found"
            details = """Make sure {0} is installed and on your PATH.\nFor more info: {1}""".format(self.command, website)  # noqa: E501
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
        if self.uses_ddash:
            self.parse_ddash_args()

    def assert_version(self, actual_ver, expected_ver):
        """--version hook arg enforces specific versions of tools."""
        expected_len = len(expected_ver)  # allows for fuzzy versions
        if expected_ver not in actual_ver[:expected_len]:
            problem = "Version of " + self.command + " is wrong"
            details = """Expected version: {0}\nFound version: {1}\nEdit your pre-commit config or use a different version of {2}.""".format(expected_ver, actual_ver, self.command)  # noqa: E501
            self.raise_error(problem, details)

    def raise_error(self, problem, details):
        """Raise a formatted error."""
        self.stderr = """Problem with {}: {}\n{}\n""".format(self.command, problem, details)
        self.returncode = 1
        sys.stderr.write(self.stderr)
        sys.exit(self.returncode)

    def get_version_str(self):
        """Get the version string like 8.0.0 for a given command."""
        args = [self.command, "--version"]
        sp_child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        version_str = str(sp_child.stdout, encoding='utf-8')
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
        else:
            self.args += ["--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]

