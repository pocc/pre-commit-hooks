#!/usr/bin/env python3
"""Wrapper script for oclint"""
###############################################################################
import difflib
import sys

from hooks.utils import Command


class ClangFormatCmd(Command):
    """Class for the ClangFormat command."""

    command = "clang-format"
    lookbehind = "clang-format version "
    uses_ddash = False

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args, self.uses_ddash)
        self.check_installed()
        self.parse_args(args)

    @staticmethod
    def format_as_diff(lines):
        """Function to remove empty diff lines, convert to bash diff format
        Python uses +/-, so convert that to </>

        For example:
            < this is
            < expected
            ---
            > and this is actual
        """
        output = []
        left_toggle = True  # to imitate bash diff
        for line in lines:
            if line[0] == "+":
                if not left_toggle:
                    output += ["\n"]
                output += ["< " + line[1:]]
                left_toggle = True
            elif line[0] == "-":
                if left_toggle:
                    output += ["---"]
                output += ["> " + line[1:]]
                left_toggle = False
        return output

    def get_clang_format_lines(self, filename: str) -> [str]:
        child = self.run_command(filename)
        if len(child.stderr) > 0:
            problem = "Unexpected Stderr received from clang-format"
            self.raise_error(problem, str(child.stderr, encoding="utf-8"))
        lines_str = str(child.stdout, encoding="utf-8")
        if lines_str == "":
            return []
        return lines_str.split('\n')

    @staticmethod
    def get_filelines(filename) -> [str]:
        with open(filename, 'rb') as f:
            filetext = f.read()
        return str(filetext, encoding="utf-8").split("\n")

    def run(self):
        """Run clang-format. Error if diff is incorrect."""
        for filename in self.files:
            actual = self.get_filelines(filename)
            expected = self.get_clang_format_lines(filename)
            if "-i" in self.args:
                # If -i is used, clang-format will fix in place with no stdout
                # So compare the before/after file for hook pass/fail
                expected = self.get_filelines(filename)
            python_diff = list(difflib.ndiff(expected, actual))
            diff = self.format_as_diff(python_diff)
            if len(diff) > 0:
                if len(expected) == 0 and "-i" in self.args:
                    # If command has no stdout, expected is meaningless.
                    sys.stdout.write("clang-format reformatted " + filename)
                else:
                    self.stderr = "\n" + "\n".join(diff) + "\n"
                    sys.stdout.write(self.stderr)
                self.returncode = 1
                sys.exit(self.returncode)


def main(argv=None):
    cmd = ClangFormatCmd(argv)
    cmd.run()


if __name__ == '__main__':
    main()
