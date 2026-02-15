#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""
import re
import sys
from typing import List

from hooks.utils import StaticAnalyzerCmd


class ClangTidyCmd(StaticAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args

    def run(self):
        """Run clang-tidy. If --fix-errors is passed in, then return code will be 0, even if there are errors."""
        for filename in self.files:
            self.run_command([filename] + self.args)
            # Warnings generated aren't important.
            pattern = re.compile(rb"[\d,]+ warning \S+\s+")
            count = sum(1 for source, msg in self.output if source == 'stderr' and not pattern.search(msg))
            if count > 0 and "--fix-errors" not in self.args:
                self.returncode = 1
            self.exit_on_error()


def main(argv: List[str] = sys.argv):
    cmd = ClangTidyCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
