#!/usr/bin/env python
"""Wrapper script for oclint"""
#############################################################################
import os
import sys

from hooks.utils import ClangAnalyzerCmd


class OCLintCmd(ClangAnalyzerCmd):
    """Class for the OCLint command."""

    command = "oclint"
    lookbehind = "OCLint version "

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.parse_ddash_args()
        # If a compilation database is not used, suppress errors
        if "-p" not in self.args:
            self.add_if_missing(["--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])

    def run(self):
        """Run OCLint and remove generated temporary files"""
        # Split text into an array of args that can be passed into oclint
        for filename in self.files:
            current_files = os.listdir(os.getcwd())
            self.run_command(filename)
            if self.returncode != 0:
                sys.stdout.write(self.stdout)
                self.returncode = 1
                sys.exit(self.returncode)
            self.parse_output()
            self.cleanup_files(current_files)

    def parse_output(self):
        """ oclint return code is usually wrong (github.com/oclint/oclint/issues/538)
        Figure out what it is based on stdout and return that instead
        """
        violations = "FilesWithViolations=0" not in self.stdout
        compiler_errors = "Compiler Errors" in self.stdout
        if violations or compiler_errors:
            output = self.stdout + self.stderr
            self.raise_error("OCLint Violations found", output)
        self.stdout = ""

    @staticmethod
    def cleanup_files(existing_files):
        """Delete the plist files that oclint generates."""
        new_files = os.listdir(os.getcwd())
        for filename in new_files:
            if filename not in existing_files and filename[-6:] == ".plist":
                os.remove(filename)


def main(argv=None):
    cmd = OCLintCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
