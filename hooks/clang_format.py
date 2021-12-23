#!/usr/bin/env python3
"""Wrapper script for clang-format"""
import sys
from typing import List

from hooks.utils import FormatterCmd


class ClangFormatCmd(FormatterCmd):
    """Class for the ClangFormat command."""

    command = "clang-format"
    lookbehind = "clang-format version "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.check_installed()
        self.parse_args(args)
        self.set_diff_flag()
        self.edit_in_place = "-i" in self.args

    def run(self):
        """Run clang-format. Error if diff is incorrect."""
        for filename in self.files:
            self.compare_to_formatted(filename)
        if self.returncode != 0:
            sys.stdout.buffer.write(self.stderr)
            sys.exit(self.returncode)


def main(argv: List[str] = sys.argv):
    cmd = ClangFormatCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
