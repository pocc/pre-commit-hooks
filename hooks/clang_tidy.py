#!/usr/bin/env python
"""Wrapper script for clang-tidy."""
#############################################################################
import sys

from hooks.utils import Command


class ClangTidyCmd(Command):
    """Class for the OCLint command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)

    def run(self):
        """Run OCLint and remove generated temporary files"""
        for filename in self.files:
            self.run_command(filename)
            self.parse_output()

    def parse_output(self):
        """clang-tidy creates warnings about systems files (i.e. non-user code)
        and sends these to stderr. Delete these three lines.

        Paradoxically, stdout indicates an error, and stderr is where
        messages from this utility are sent."""
        output = self.stderr
        self.stderr = ""
        for line in output.split("\n"):
            if not (
                " warnings generated" in line
                or "in non-user-code" in line
                or "non system headers. Use -system-headers" in line
            ):
                self.stderr += line + "\n"
        self.stderr = self.stderr.strip()  # Remove extra newlines just added
        if len(self.stderr) > 0 or len(self.stdout) > 0:
            self.retcode = 1


def main(argv=[]):
    cmd = ClangTidyCmd(argv)
    cmd.run()
    cmd.pipe_to_std_files()
    return cmd.retcode


if __name__ == '__main__':
    main()
