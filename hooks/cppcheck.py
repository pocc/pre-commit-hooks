#!/usr/bin/env python3
"""Wrapper script for cppcheck."""
#############################################################################
import sys

from hooks.utils import Command


class CppcheckCmd(Command):
    """Class for the cppcheck command."""

    command = "cppcheck"
    lookbehind = "Cppcheck "

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        # quiet for stdout purposes
        self.add_if_missing(["-q"])
        # make cppcheck behave as expected for pre-commit
        self.add_if_missing(["--error-exitcode=1"])
        # Enable all of the checks
        self.add_if_missing(["--enable=all"])

    def run(self):
        """Run cppcheck"""
        for filename in self.files:
            child = self.run_command(filename)
            self.stdout = str(child.stdout, encoding="utf-8")
            # Useless error see https://stackoverflow.com/questions/6986033
            useless_error_part = (
                b"(information) Cppcheck cannot " b"find all the include files"
            )
            if useless_error_part in child.stderr:
                child.stderr = b""
            self.stderr = str(child.stderr, encoding="utf-8")
            self.returncode = child.returncode
            if child.returncode != 0:
                sys.stderr.buffer.write(child.stderr)
                sys.exit(child.returncode)


def main(argv=None):
    cmd = CppcheckCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
