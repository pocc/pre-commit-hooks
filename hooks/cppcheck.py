#!/usr/bin/env python3
"""Wrapper script for cppcheck."""
import sys
from typing import List

from hooks.utils import StaticAnalyzerCmd


class CppcheckCmd(StaticAnalyzerCmd):
    """Class for the cppcheck command."""

    command = "cppcheck"
    lookbehind = "Cppcheck "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        # quiet for stdout purposes
        self.add_if_missing(["-q"])
        # make cppcheck behave as expected for pre-commit
        self.add_if_missing(["--error-exitcode=1"])
        # Enable all of the checks
        self.add_if_missing(["--enable=all"])
        # Per https://github.com/pocc/pre-commit-hooks/pull/30, suppress missingIncludeSystem messages.
        # allow_multiple so a user supplied --suppress adds to these rather than replacing them.
        suppressions = ["--suppress=unmatchedSuppression", "--suppress=missingIncludeSystem"]
        # unusedFunction false-positives on a partial file set (a function whose only caller
        # is not staged looks unused), so suppress it by default. With --project cppcheck sees
        # the whole program, so the check is valid there and must not be forced off.
        if not any(arg.startswith("--project") for arg in self.args):
            suppressions.append("--suppress=unusedFunction")
        self.add_if_missing(suppressions, allow_multiple=True)

    def run(self):
        """Run cppcheck.

        --project supplies the file list itself and cppcheck rejects source files
        alongside it ("--project cannot be used in conjunction with source files"),
        so in that mode run once and do not append the committed files.
        """
        if any(arg.startswith("--project") for arg in self.args):
            self.run_command(self.args)
            self.exit_on_error()
            return
        for filename in self.files:
            self.run_command([filename] + self.args)
            self.exit_on_error()


def main(argv: List[str] = sys.argv):
    cmd = CppcheckCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
