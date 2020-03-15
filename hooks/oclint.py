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

    def __init__(self, args=sys.argv):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)

    def run(self):
        """Run OCLint and remove generated temporary files"""
        # Split text into an array of args that can be passed into oclint
        for filename in self.files:
            current_files = os.listdir()
            self.run_command(filename)
            self.parse_output()
            self.cleanup(current_files)

    def parse_output(self):
        """ oclint return code is usually wrong (github.com/oclint/oclint/issues/538)
        Figure out what it is based on stdout and return that instead
        clang-tidy can complain about # of warnings in systems files
        """
        no_errors = "FilesWithViolations=0"
        if no_errors not in self.stdout:
            self.raise_error("OCLint Violations found", "")

    @staticmethod
    def cleanup(existing_files):
        """Delete the plist files that oclint generates."""
        new_files = os.listdir()
        for filename in new_files:
            if filename not in existing_files:
                os.remove(filename)


def main():
    cmd = OCLintCmd()
    cmd.run()
    cmd.pipe_to_std_files()
    return cmd.retcode


if __name__ == '__main__':
    main()
