#!/usr/bin/env python
"""Wrapper script for oclint"""
#############################################################################
import os

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
            child = self.run_command(filename)
            if child.returncode != 0:
                details = str(child.stdout + child.stderr, encoding="utf-8")
                self.raise_error("Problem running OCLint", details)
            self.parse_output(child.stdout, child.stderr)
            self.cleanup(current_files)

    def parse_output(self, stdout, stderr):
        """ oclint return code is usually wrong (github.com/oclint/oclint/issues/538)
        Figure out what it is based on stdout and return that instead
        """
        no_errors = b"FilesWithViolations=0"
        if no_errors not in stdout:
            output = str(stdout + stderr, encoding="utf-8")
            self.raise_error("OCLint Violations found", output)

    @staticmethod
    def cleanup(existing_files):
        """Delete the plist files that oclint generates."""
        new_files = os.listdir(os.getcwd())
        for filename in new_files:
            if filename not in existing_files:
                os.remove(filename)


def main(argv=None):
    cmd = OCLintCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
