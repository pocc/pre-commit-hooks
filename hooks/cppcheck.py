#!/usr/bin/env python3
"""Wrapper script for cppcheck."""
import hashlib
import os
import sys
from contextlib import nullcontext
from typing import List

from hooks.utils import file_lock
from hooks.utils import StaticAnalyzerCmd

BUILD_DIR_OPTION = "--cppcheck-build-dir"
NO_CACHE_OPTION = "--no-cppcheck-cache"


class CppcheckCmd(StaticAnalyzerCmd):
    """Class for the cppcheck command."""

    command = "cppcheck"
    lookbehind = "Cppcheck "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.no_cache = NO_CACHE_OPTION in self.args
        if self.no_cache:
            self.args.remove(NO_CACHE_OPTION)
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
        if not any(arg == "-j" or arg.startswith("-j") for arg in self.args):
            self.args += ["-j", str(os.cpu_count() or 1)]

    def get_cache_root(self):
        """Return the configured cppcheck build directory, if any."""
        build_arg = next(
            (arg for arg in self.args if arg.startswith(BUILD_DIR_OPTION + "=")),
            None,
        )
        if self.no_cache:
            if build_arg:
                self.raise_error(
                    "Conflicting cppcheck cache options",
                    f"Use {NO_CACHE_OPTION} or {BUILD_DIR_OPTION}=<path>, not both.",
                )
            return None
        if build_arg:
            return build_arg.split("=", 1)[1]
        if os.name == "nt":
            cache_home = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        elif sys.platform == "darwin":
            cache_home = os.path.expanduser("~/Library/Caches")
        else:
            cache_home = os.environ.get(
                "XDG_CACHE_HOME", os.path.expanduser("~/.cache")
            )
        repository = os.path.normcase(os.path.abspath(os.getcwd()))
        repository_hash = hashlib.sha256(repository.encode()).hexdigest()
        cache_root = os.path.join(
            cache_home,
            "pre-commit-hooks",
            "cppcheck",
            self.get_version_str(),
            repository_hash,
        )
        self.args.append(f"{BUILD_DIR_OPTION}={cache_root}")
        return cache_root

    def run(self):
        """Run cppcheck.

        --project supplies the file list itself and cppcheck rejects source files
        alongside it ("--project cannot be used in conjunction with source files"),
        so in that mode run once and do not append the committed files.

        The normal hook passes one file list to cppcheck so all selected files
        share a coherent build directory.
        """
        cache_root = self.get_cache_root()
        if cache_root:
            os.makedirs(cache_root, exist_ok=True)
        lock = (
            file_lock(os.path.join(cache_root, ".lock")) if cache_root else nullcontext()
        )
        with lock:
            if any(arg.startswith("--project") for arg in self.args):
                self.run_command(self.args)
            else:
                self.run_command(
                    self.args + ["--file-list=-"], "\n".join(self.files).encode()
                )
            self.exit_on_error()


def main(argv: List[str] = sys.argv):
    cmd = CppcheckCmd(argv)
    cmd.run()


if __name__ == "__main__":
    main()
