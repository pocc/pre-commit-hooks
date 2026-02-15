#!/usr/bin/env python3
"""Wrapper script for cppcheck."""
import re
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
        # Per https://github.com/pocc/pre-commit-hooks/pull/30, suppress missingIncludeSystem messages
        self.add_if_missing(
            ["--suppress=unmatchedSuppression", "--suppress=missingIncludeSystem", "--suppress=unusedFunction"]
        )

    def run(self):
        """Run cppcheck"""
        self.run_command(
            self.args + ["--file-list=-"],
            input_data="\n".join(self.files).encode(),
            env={"CLICOLOR_FORCE": "1"}
        )
        self.post_process_output(filter=r"[^:]+:\d+:\d+: .+", unique=True)
        self.exit_on_error()


def main(argv: List[str] = sys.argv):
    cmd = CppcheckCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
