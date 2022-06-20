import re
import sys
from typing import List
import multiprocessing as mp

from hooks.utils import StaticAnalyzerCmd


class ClangTidyCmd(StaticAnalyzerCmd):
    """Class for the clang-tidy command."""

    command = "clang-tidy"
    lookbehind = "LLVM version "

    def __init__(self, args: List[str]):
        super().__init__(self.command, self.lookbehind, args)
        self.parse_args(args)
        self.edit_in_place = "-fix" in self.args or "--fix-errors" in self.args

    def tidy_file(self, filename: List[str]):
        self.run_command([filename] + self.args)
        # Warnings generated aren't important.
        self.stderr = re.sub(rb"[\d,]+ warning \S+\s+", b"", self.stderr)
        if len(self.stderr) > 0 and "--fix-errors" in self.args:
            self.returncode = 1
        return self.returncode, self.stderr

    def run(self):
        """Run clang-tidy. If --fix-errors is passed in, then return code will be 0, even if there are errors."""
        with mp.Pool(mp.cpu_count()) as p:
            results = p.map(self.tidy_file, self.files)
            ret_codes, stderrs = zip(*results)

            self.returncode = max(ret_codes)
            self.stderr = b"\n".join(stderrs)
            self.exit_on_error()
