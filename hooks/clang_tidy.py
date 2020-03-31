#!/usr/bin/env python3
"""Wrapper script for clang-tidy."""
#############################################################################
import re
import sys

from hooks.utils import ClangAnalyzerCmd


class ClangTidyCmd(ClangAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args
        self.parse_ddash_args()
        # If a compilation database is not used, suppress errors
        cdb_found = False
        for arg in self.args:
            if arg.startswith("-p"):
                cdb_found = True
                break
        if not cdb_found:
            self.add_if_missing(["--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"])
        # Enable all of the checks
        self.add_if_missing(["-checks=*"])

    def run(self):
        """Run clang-tidy"""
        for filename in self.files:
            self.run_command(filename)
            sys.stdout.write(self.stdout)
            # The number of warnings depends on errors in system files
            self.stderr = re.sub(r"\d+ warnings and ", "", self.stderr)
            # Don't output stderr if it's complaining about problems in system files
            no_sysfile_warning = "non-user code" not in self.stderr
            # On good clang-tidy checks, it will spew warnings to stderr
            if len(self.stdout) > 0 and no_sysfile_warning:
                sys.stderr.write(self.stderr)
            else:
                self.stderr = ""
            has_errors = (
                "error generated." in self.stderr
                or "errors generated." in self.stderr
            )
            if has_errors:  # Change return code if errors are generated
                self.returncode = 1
            if self.returncode != 0:
                sys.exit(self.returncode)


def main(argv=None):
    cmd = ClangTidyCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
