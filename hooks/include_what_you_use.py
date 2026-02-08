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
            # IWYU expects: <clang opts> <source file> not <source file> <clang opts>
            # See: https://github.com/pocc/pre-commit-hooks/issues/49
            self.run_command(self.args + [filename])
            is_correct = b"has correct #includes/fwd-decls" in self.stderr
            if is_correct:
                self.returncode = 0
                self.stdout = b""
                self.stderr = b""
            else:
                # IWYU exit codes: 0=success, 1=suggestions, 2=error, 3+=fatal error
                # We should fail on any non-zero exit code or when includes are incorrect
                # See: https://github.com/pocc/pre-commit-hooks/issues/55
                if self.returncode == 0:
                    # If IWYU didn't set a proper exit code but includes are wrong, force failure
                    self.returncode = 1
                sys.stderr.buffer.write(self.stdout + self.stderr)
                sys.exit(self.returncode)


def main(argv: List[str] = sys.argv):
    cmd = IncludeWhatYouUseCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
