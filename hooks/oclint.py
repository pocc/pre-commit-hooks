#!/usr/bin/env python
"""Wrapper script for oclint"""
#############################################################################
import os
import sys

from hooks.utils import Command


class OCLintCmd(Command):
    """Class for the OCLint command."""

    command = "oclint"
    lookbehind = "OCLint version "
    uses_ddash = True

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args, self.uses_ddash)
        self.parse_args(args)

    def run(self):
        """Run OCLint and remove generated temporary files"""
        # Split text into an array of args that can be passed into oclint
        for filename in self.files:
            current_files = os.listdir()
            child = self.run_command(filename)
            if child.returncode != 0:
                details = str(child.stdout + child.stderr, encoding="utf-8")
                self.raise_error("Problem running OCLint", details)
            self.parse_output(child.stdout, child.stderr)
            self.cleanup(current_files)

    def parse_output(self, stdout, stderr):
        """ oclint return code is usually wrong (github.com/oclint/oclint/issues/538)
        Figure out what it is based on stdout and return that instead
        clang-tidy can complain about # of warnings in systems files
        """
        no_errors = b"FilesWithViolations=0"
        if no_errors not in stdout:
            output = str(stdout + stderr, encoding="utf-8")
            self.raise_error("OCLint Violations found", output)

    @staticmethod
    def cleanup(existing_files):
        """Delete the plist files that oclint generates."""
        new_files = os.listdir()
        for filename in new_files:
            if filename not in existing_files:
                os.remove(filename)


def main(argv=None):
    cmd = OCLintCmd(argv)
    cmd.run()


if __name__ == '__main__':
    main()
