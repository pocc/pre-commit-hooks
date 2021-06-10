#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wrapper for include-what-you-use"""
# ==============================================================================
import shutil
import sys

from hooks.utils import Command


class IncludeWhatYouUseCmd(Command):
    """Class for the Include-What-You-Use command."""

    command = "include-what-you-use"
    lookbehind = "include-what-you-use "

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.check_installed()
        self.parse_args(args)

    def run(self):
        """Run Include-What-You-Use. Error if diff is incorrect."""

        error_output = []
        for filename in self.files:
            self.run_command(filename)
            error_output.append(self.parse_output())

        if error_output:
            self.raise_error("Include-What-You-Use violations found\n", "".join(error_output))

    def parse_output(self):
        """Include-What-You-Use return code is never 0
        Figure out what it is based on stdout and return that instead
        """
        is_correct = "has correct #includes/fwd-decls" in self.stderr

        if not is_correct and self.stderr:
            output = self.stdout + self.stderr
            self.stdout = ""
            self.stderr = ""
            return output
        return []


def main(argv=None):
    cmd = IncludeWhatYouUseCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
