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
        self.set_line_diff_flag()
        self.set_no_diff_flag()
        self.set_no_diff_flag()
        self.edit_in_place = "-i" in self.args

    def run(self):
        """Run clang-format. Error if diff is incorrect."""
        for filename in self.files:
            options: List[str] = []
            if self.line_diff_flag and filename in self.changed_lines:
                for range in self.changed_lines[filename]:
                    options += ["-lines", f"{range[0]}:{range[1]}"]
            self.compare_to_formatted(filename, options)


def main(argv: List[str] = sys.argv):
    cmd = ClangFormatCmd(argv)
    cmd.run()
    cmd.exit_on_error()


if __name__ == "__main__":
    main()
