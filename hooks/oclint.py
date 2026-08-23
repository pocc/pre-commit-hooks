#!/usr/bin/env python
"""Wrapper script for oclint"""
import os
import re
import sys
from typing import List

from hooks.utils import StaticAnalyzerCmd


class OCLintCmd(StaticAnalyzerCmd):
    """Class for the OCLint command."""

    command = "oclint"
    lookbehind = "OCLint version "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.version = self.get_version_str()
        self.parse_args(args)
        # Earlier versions (0.13.1 and before) have -no-analytics and 1 dash instead of 2 for args
        if self.version >= "20":
            # Check for as many errors as possible (see https://github.com/oclint/oclint/issues/538)
            self.add_if_missing(["--max-priority-3", "0"])
            # Enable different classes of analysis
            self.add_if_missing(["--enable-global-analysis", "--enable-clang-static-analyzer"])
        else:
            # Check for as many errors as possible (see https://github.com/oclint/oclint/issues/538)
            self.add_if_missing(["-max-priority-3", "0"])
            # Enable different classes of analysis
            self.add_if_missing(["-enable-global-analysis", "-enable-clang-static-analyzer"])
            # Sending analytics can cause oclint to hang, but is not an option in later versions.
            self.add_if_missing(["-no-analytics"])

    def run(self):
        """Run OCLint and remove generated temporary files. OCLint will put the standard report into stderr."""
        # OCLint runs once per file to provide per-file analysis
        # See: https://github.com/pocc/pre-commit-hooks/issues/45
        total_files = len(self.files)
        for idx, filename in enumerate(self.files, 1):
            # Print progress for multiple files
            if total_files > 1:
                sys.stderr.buffer.write(f"\n[OCLint {idx}/{total_files}] Analyzing {filename}\n".encode())

            current_files = os.listdir(os.getcwd())
            self.run_command([filename] + self.args)
            # OCLint writes its report to stdout, so promote it to stderr when it
            # found something. This covers rule violations, not just compiler errors.
            if self.has_findings(self.stdout):
                self.stderr = self.stdout
            # If errors have been captured, stdout is unexpected
            self.stdout = b""
            self.exit_on_error()
            self.cleanup_files(current_files)

    @staticmethod
    def has_findings(stdout: bytes) -> bool:
        """Whether OCLint reported anything that should fail the hook.

        OCLint prints its report to stdout. Two independent signals matter, and
        only checking for the word "Errors" (see #45) missed the second:

        - compiler errors appear under a "Compiler Errors" heading
        - rule violations are summarised as "FilesWithViolations=N"; a clean run
          reports N=0, and a file that failed to compile reports N=0 as well, so
          the count alone is not sufficient and neither signal subsumes the other.
        """
        if b"Compiler Errors" in stdout:
            return True
        match = re.search(rb"FilesWithViolations=(\d+)", stdout)
        return bool(match and int(match.group(1)) > 0)

    @staticmethod
    def cleanup_files(existing_files: List[str]):
        """Delete the plist files that oclint generates."""
        new_files = os.listdir(os.getcwd())
        for filename in new_files:
            if filename not in existing_files and filename[-6:] == ".plist":
                os.remove(filename)


def main(argv: List[str] = sys.argv):
    cmd = OCLintCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
