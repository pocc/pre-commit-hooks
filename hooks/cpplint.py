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
        """Run cpplint"""
        error_occurred = False
        for filename in self.files:
            self.run_command_cpplint(self.args + [filename])  # cpplint is unique in requiring args before filename
            if self.returncode != 0:
                error_occurred = True

        if error_occurred:
            sys.exit(1)


def main(argv: List[str] = sys.argv):
    cmd = CpplintCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
