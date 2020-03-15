#!/usr/bin/env python
"""Wrapper script for oclint"""
###############################################################################
import difflib
import sys

from hooks.utils import Command


class ClangFormatCmd(Command):
    """Class for the ClangFormat command."""

    command = "clang-format"
    lookbehind = "clang-format version "

    def __init__(self, args=sys.argv):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)

    @staticmethod
    def filter_lines(lines):
        """Function to remove empty diff lines and convert to diff format"""
        output = []
        left_toggle = False  # to imitate bash diff
        for line in lines:
            if line[0] == "-":
                if left_toggle:
                    output += ["---"]
                    left_toggle = False
                output += ["> " + line[1:]]
            elif line[0] == "+":
                output += ["< " + line[1:]]
                left_toggle = True
        return output

    def run(self):
        """Run clang-format. Error if diff is incorrect."""
        for filename in self.files:
            self.run_command(filename)
            with open(filename) as f:
                filetext = f.read()
            diff = difflib.ndiff(self.stdout.split("\n"), filetext.split("\n"))
            diff_list = self.filter_lines(diff)
            diff_lines = "\n".join(diff_list)
            self.stdout = ""
            if len(diff_lines) > 0:
                self.stdout = "\n" + "".join(diff_lines) + "\n"
                self.retcode = 1
                return


def main():
    cmd = ClangFormatCmd()
    cmd.run()
    cmd.pipe_to_std_files()
    return cmd.retcode


if __name__ == '__main__':
    main()
