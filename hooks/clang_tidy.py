#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""
#############################################################################
import re
import sys

from hooks.utils import ClangAnalyzerCmd


class ClangTidyCmd(ClangAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args
        self.parse_ddash_args()

    def run(self):
        """Run clang-tidy"""
        for filename in self.files:
            self.run_command(filename)
            sys.stdout.buffer.write(self.stdout)
            # The number of warnings depends on errors in system files
            self.stderr = re.sub(b"\d+ warnings and ", b"", self.stderr)
            # Don't output stderr if it's complaining about problems in system files
            no_sysfile_warning = b"non-user code" not in self.stderr
            # On good clang-tidy checks, it will spew warnings to stderr
            if len(self.stdout) > 0 and no_sysfile_warning:
                sys.stderr.buffer.write(self.stderr)
            else:
                self.stderr = b""
            has_errors = (
                b"error generated." in self.stderr
                or b"errors generated." in self.stderr
            )
            if has_errors:  # Change return code if errors are generated
                self.returncode = 1
            if self.returncode != 0:
                sys.exit(self.returncode)


def main(argv=None):
    cmd = ClangTidyCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
