#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""
#############################################################################
import sys

from hooks.utils import Command


class ClangTidyCmd(Command):
    """Class for the OCLint command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "
    uses_ddash = True

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args, self.uses_ddash)
        self.parse_args(args)

    def run(self):
        """Run OCLint and remove generated temporary files"""
        for filename in self.files:
            child = self.run_command(filename)
            self.stdout = str(child.stdout, encoding="utf-8")
            sys.stdout.buffer.write(child.stdout)
            # Don't output stderr if it's complaining about problems in system files
            if len(child.stdout) > 0 and b"warnings generated" not in child.stderr:
                self.stderr = str(child.stderr, encoding="utf-8")
                sys.stderr.buffer.write(child.stderr)
            if child.returncode != 0:
                self.returncode = child.returncode
                sys.exit(child.returncode)


def main(argv=None):
    cmd = ClangTidyCmd(argv)
    cmd.run()


if __name__ == '__main__':
    main()
