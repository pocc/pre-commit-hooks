#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""
import re
import sys
import json
from typing import List

from hooks.utils import StaticAnalyzerCmd


class ClangTidyCmd(StaticAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.set_line_diff_flag()
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args

    def run(self):
        """Run clang-tidy. If --fix-errors is passed in, then return code will be 0, even if there are errors."""
        for filename in self.files:
            line_diff_arg = []
            if self.line_diff_flag:
                # clang-tidy help gives this JSON as reference: [{"name":"file1.cpp","lines":[[1,3],[5,7]]},{"name":"file2.h"}]
                line_diff_prefix = "-line-filter="
                ct_json_changed_lines = [{"name": name, "lines": self.changed_lines[name]} for name in self.changed_lines]
                line_diff_arg = [line_diff_prefix + json.dumps(ct_json_changed_lines)]

            self.run_command([filename] + self.args + line_diff_arg)
            # Warnings generated aren't important.
            self.stderr = re.sub(rb"[\d,]+ warning \S+\s+", b"", self.stderr)
            if len(self.stderr) > 0 and "--fix-errors" in self.args:
                self.returncode = 1


def main(argv: List[str] = sys.argv):
    cmd = ClangTidyCmd(argv)
    cmd.run()
    cmd.exit_on_error()

if __name__ == "__main__":
    main()
