#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper for include-what-you-use"""
import sys
from typing import List

from hooks.utils import StaticAnalyzerCmd


class IncludeWhatYouUseCmd(StaticAnalyzerCmd):
    """Class for the Include-What-You-Use command."""

    command = "include-what-you-use"
    lookbehind = "include-what-you-use "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.check_installed()
        self.parse_args(args)

    def run(self):
        """Run Include-What-You-Use. Error if includes/forward declarations are incorrect."""

        for filename in self.files:
            self.run_command([filename] + self.args)
            is_correct = b"has correct #includes/fwd-decls" in self.stderr
            if is_correct:
                self.returncode = 0
                self.stdout = b""
                self.stderr = b""
            else:
                sys.stderr.buffer.write(self.stdout + self.stderr)
                sys.exit(self.returncode)


def main(argv: List[str] = sys.argv):
    cmd = IncludeWhatYouUseCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
