#!/usr/bin/env python3
"""Wrapper script for cppcheck."""
import hashlib
import os
import sys
from typing import List

from hooks.utils import file_lock
from hooks.utils import StaticAnalyzerCmd

BUILD_DIR_OPTION = "--cppcheck-build-dir"


class CppcheckCmd(StaticAnalyzerCmd):
    """Class for the cppcheck command."""

    command = "cppcheck"
    lookbehind = "Cppcheck "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        # quiet for stdout purposes
        self.add_if_missing(["-q"])
        # make cppcheck behave as expected for pre-commit
        self.add_if_missing(["--error-exitcode=1"])
        # Enable all of the checks
        self.add_if_missing(["--enable=all"])
        # Per https://github.com/pocc/pre-commit-hooks/pull/30, suppress missingIncludeSystem messages.
        # allow_multiple so a user supplied --suppress adds to these rather than replacing them.
        suppressions = ["--suppress=unmatchedSuppression", "--suppress=missingIncludeSystem"]
        # unusedFunction false-positives on a partial file set (a function whose only caller
        # is not staged looks unused), so suppress it by default. With --project cppcheck sees
        # the whole program, so the check is valid there and must not be forced off.
        if not any(arg.startswith("--project") for arg in self.args):
            suppressions.append("--suppress=unusedFunction")
        self.add_if_missing(suppressions, allow_multiple=True)

    def run(self):
        """Run cppcheck.

        --project supplies the file list itself and cppcheck rejects source files
        alongside it ("--project cannot be used in conjunction with source files"),
        so in that mode run once and do not append the committed files.

        When a build directory is configured, each source gets its own cache so
        parallel analysis of different sources does not share cache files.
        """
        build_arg = next((arg for arg in self.args if arg.startswith(BUILD_DIR_OPTION + "=")), None)
        cache_root = build_arg.split("=", 1)[1] if build_arg else None
        if any(arg.startswith("--project") for arg in self.args):
            if cache_root:
                os.makedirs(cache_root, exist_ok=True)
                with file_lock(os.path.join(cache_root, ".lock")):
                    self.run_command(self.args)
                    self.exit_on_error()
            else:
                self.run_command(self.args)
                self.exit_on_error()
            return

        for filename in self.files:
            args = self.args
            if cache_root:
                source_path = os.path.normcase(os.path.abspath(filename))
                cache_dir = os.path.join(cache_root, hashlib.sha256(source_path.encode()).hexdigest())
                os.makedirs(cache_dir, exist_ok=True)
                args = [f"{BUILD_DIR_OPTION}={cache_dir}" if arg == build_arg else arg for arg in self.args]
                with file_lock(os.path.join(cache_dir, ".lock")):
                    self.run_command([filename] + args)
                    self.exit_on_error()
            else:
                self.run_command([filename] + args)
                self.exit_on_error()


def main(argv: List[str] = sys.argv):
    cmd = CppcheckCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
