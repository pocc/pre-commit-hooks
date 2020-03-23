#!/usr/bin/env python3
"""Wrapper script for uncrustify"""
###############################################################################
import os
import re
import subprocess as sp

from hooks.utils import FormatterCmd


class UncrustifyCmd(FormatterCmd):
    """Class for the uncrustify command."""

    command = "uncrustify"
    lookbehind = "Uncrustify-"

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.check_installed()
        self.parse_args(args)
        self.file_flag = "-f"
        self.edit_in_place = "--replace" in self.args
        if "-c" not in self.args:
            self.fix_defaults()
            self.add_if_missing(["-c", "defaults.cfg"])

    @staticmethod
    def fix_defaults():
        """If defaults file doesn't exist, create and write it
        This is required and uncrustify will error if one is not provided"""
        if "defaults.cfg" not in os.listdir():
            # --show-config prints the current config to stdout
            cmds = ["uncrustify", "--show-config"]
            defaults = sp.check_output(cmds).decode("utf-8")
            # Change default 8 => 2 spaces per LLVM default
            regex = r"(indent_columns\s+=) \d"
            defaults = re.sub(regex, r"\1 2", defaults)
            with open("defaults.cfg", "w") as f:
                f.write(defaults)

    def run(self):
        """Run uncrustify with the arguments provided."""
        for filename in self.files:
            self.compare_to_formatted(filename)


def main(argv=None):
    cmd = UncrustifyCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
