#!/usr/bin/env python3
"""Wrapper script for cpplint."""
import sys
from typing import List

from hooks.utils import StaticAnalyzerCmd


class CpplintCmd(StaticAnalyzerCmd):
    """Class for the cpplint command."""

    command = "cpplint"
    lookbehind = "cpplint "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.add_if_missing(["--verbose=0"])

    def run(self):
        """Run cpplint on every file before exiting, so all errors are reported.

        cpplint is invoked per file. Exiting inside the loop stopped at the first
        file with errors and hid the rest, forcing repeated commit attempts. Run
        them all, keep the worst return code, then exit once. run_command already
        accumulates stdout/stderr across calls.
        """
        returncode = 0
        for filename in self.files:
            self.run_command(self.args + [filename])  # cpplint is unique in requiring args before filename
            returncode = max(returncode, self.returncode)
        self.returncode = returncode
        self.exit_on_error()


def main(argv: List[str] = sys.argv):
    cmd = CpplintCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
