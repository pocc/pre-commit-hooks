#!/usr/bin/env python3
"""Wrapper script for uncrustify"""
import os
import re
import subprocess as sp
import sys
from typing import List

from hooks.utils import FormatterCmd


class UncrustifyCmd(FormatterCmd):
    """Class for the uncrustify command."""

    command = "uncrustify"
    lookbehind = "[uU]ncrustify[- ]"

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.check_installed()
        self.parse_args(args)
        self.set_no_diff_flag()
        self.set_no_diff_flag()
        self.add_if_missing(["-q"])  # Remove stderr, which causes issues
        self.file_flag = "-f"
        self.edit_in_place = "--replace" in self.args
        if "-c" not in self.args:
            self.fix_defaults()
            self.add_if_missing(["-c", "defaults.cfg"])

    @staticmethod
    def fix_defaults():
        """If defaults file doesn't exist, create and write it
        This is required and uncrustify will error if one is not provided"""
        if "defaults.cfg" not in os.listdir(os.getcwd()):
            # --show-config prints the current config to stdout
            cmds = ["uncrustify", "--show-config"]
            defaults = sp.check_output(cmds)
            # Change default 8 => 2 spaces per LLVM default
            regex = rb"indent_columns.*"
            defaults = re.sub(regex, b"indent_columns = 2", defaults)
            with open("defaults.cfg", "wb") as f:
                f.write(defaults)

    def run(self):
        """Run uncrustify with the arguments provided."""
        for filename in self.files:
            options: List[str] = []  # For line diffs at some point
            self.compare_to_formatted(filename, options)

def main(argv: List[str] = sys.argv):
    cmd = UncrustifyCmd(argv)
    cmd.run()
    cmd.exit_on_error()


if __name__ == "__main__":
    main()
