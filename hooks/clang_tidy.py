#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""
#############################################################################
import sys

from hooks.utils import ClangAnalyzerCmd


class ClangTidyCmd(ClangAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "
    defaults = ["-checks=*"]

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args
        self.parse_ddash_args()
        # If a compilation database is not used, suppress errors
        if "-p" not in self.args:
            self.add_if_missing(["--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])
        # Enable all of the checks
        self.add_if_missing(["-enable-clang-static-analyzer"])

    def run(self):
        """Run clang-tidy"""
        for filename in self.files:
            child = self.run_command(filename)
            self.stdout = str(child.stdout, encoding="utf-8")
            sys.stdout.buffer.write(child.stdout)
            # Don't output stderr if it's complaining about problems in system files
            sysfile_warning = b"warnings generated" not in child.stderr
            if len(child.stdout) > 0 and sysfile_warning:
                self.stderr = str(child.stderr, encoding="utf-8")
                sys.stderr.buffer.write(child.stderr)
            if child.returncode != 0:
                self.returncode = child.returncode
                sys.exit(child.returncode)


def main(argv=None):
    cmd = ClangTidyCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
