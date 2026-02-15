#!/usr/bin/env python
"""Wrapper script for oclint"""
import os
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
                self.output.append(('stdout', f"\n[OCLint {idx}/{total_files}] Analyzing {filename}\n".encode()))

            current_files = os.listdir(os.getcwd())
            self.run_command([filename] + self.args)
            # Errors are sent to stdout instead of stderr
            if any(src == 'stdout' and b"Errors" in msg for src, msg in self.output):
                self.output = [
                        ('stderr' if src == 'stdout' else 'stdout' if src == 'stderr' else src, msg)
                        for src, msg in self.output
                        ]
            self.exit_on_error()
            self.cleanup_files(current_files)

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
