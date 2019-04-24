#!/usr/bin/env python3
"""Tests clang-format, clang-tidy, and oclint against .c and .cpp
With this snippet:

    int main() {  int i;  return 10;}

- Triggers clang-format because what should be on 4 lines is on 1
- Triggers clang-tidy because "magical number" 10 is used
- Triggers oclint because short variable name is used
"""
import os
import re
import subprocess as sp

import pytest


class TestCLinters:
    """Test all C Linters: clang-format, clang-tidy, and oclint."""

    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests.

        "err" files are expected to error for all linters
        "ok" files are expected to pass for all listers
        """
        errfiles = ["tests/files/err.c", "tests/files/err.cpp"]
        okfiles = ["tests/files/ok.c", "tests/files/ok.cpp"]
        cls.errfiles = [os.path.abspath(filename) for filename in errfiles]
        cls.okfiles = [os.path.abspath(filename) for filename in okfiles]

    def test_clang_format_ok(self):
        self.run_clang_format(
            filelist=self.okfiles, expected_output="", expected_retcode=0
        )

    def test_clang_format_err(self):
        clang_format_err = r"""1c1,4
< int main() { int i; return 10; }
---
> int main() {
>   int i;
>   return 10;
> }
"""
        self.run_clang_format(
            filelist=self.errfiles,
            expected_output=clang_format_err,
            expected_retcode=1,
        )

    @staticmethod
    def run_clang_format(filelist, expected_output, expected_retcode):
        """Test that oclint returns correct retcode & output for files.

        Use google style, printing a format diff to stdout."""
        for filename in filelist:
            print("Analyzing file", filename)
            _pipe = sp.Popen(
                ["hooks/clang-format", filename],
                text=True,
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
            )
            actual = _pipe.communicate()[0]
            # Expecting error text with a err return code
            assert actual == expected_output
            assert _pipe.returncode == expected_retcode

    def test_clang_tidy_ok(self):
        self.run_clang_tidy(
            filelist=self.okfiles, expected_output="", expected_retcode=0
        )

    def test_clang_tidy_err(self):
        clang_tidy_error = r"""{0}:1:28: error: 10 is a magic number; consider replacing it with a named constant [cppcoreguidelines-avoid-magic-numbers,-warnings-as-errors]
int main() {{ int i; return 10; }}
                           ^
"""  # noqa: E501
        self.run_clang_tidy(
            filelist=self.errfiles,
            expected_output=clang_tidy_error,
            expected_retcode=1,
        )

    def run_clang_tidy(self, filelist, expected_output, expected_retcode):
        """Test that clang tidy returns correct retcode & output for files."""
        cmds = [
            "./hooks/clang-tidy",
            "-quiet",
            "-checks=*",
            "-warnings-as-errors=*",
        ]
        for filename in filelist:
            print("Analyzing file", filename)
            expected = expected_output.format(filename)
            # In case num warnings changes due to more checks
            actual, retcode = self.get_all_output(cmds, filename)
            print(actual, retcode)
            actual = re.sub(r"^\d+", "2", actual)
            # Expecting error text with a err return code
            assert actual == expected
            assert retcode == expected_retcode

    @pytest.mark.slow
    def test_oclint_ok(self):
        self.run_oclint(
            filelist=self.okfiles, expected_output="", expected_retcode=0
        )

    @pytest.mark.slow
    def test_oclint_err(self):
        oclint_stdout_err = r"""

OCLint Report

Summary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2

{0}:1:14: short variable name [naming|P3] Length of variable name `i` is 1, which is shorter than the threshold of 3
{0}:1:14: unused local variable [unused|P3] The local variable 'i' is unused.

[OCLint (http://oclint.org) v0.13]
"""  # noqa: E501 W291
        self.run_oclint(
            filelist=self.errfiles,
            expected_output=oclint_stdout_err,
            expected_retcode=1,
        )

    def run_oclint(self, filelist, expected_output, expected_retcode):
        """Test that oclint returns correct retcode & output for files."""
        cmds = [
            "./hooks/oclint",
            "-enable-global-analysis",
            "-enable-clang-static-analyzer",
        ]
        for filename in filelist:
            print("Analyzing file", filename)
            expected = expected_output.format(filename)
            actual, retcode = self.get_all_output(cmds, filename)
            # Expecting error text with a err return code
            assert actual == expected
            assert retcode == expected_retcode

    @staticmethod
    def get_all_output(cmds, filename):
        """Helper fn to get stderr and stdout from llvm command.

        Args:
            cmds (list): List of commands to send to Popen
            filename (str): Name of file to run commands against
        Returns (tuple):
            Text output of function, return code
        """
        combined_cmds = cmds + [filename]
        _pipe = sp.Popen(
            combined_cmds, stderr=sp.STDOUT, stdout=sp.PIPE, text=True
        )
        return _pipe.communicate()[0], _pipe.returncode

    @classmethod
    def teardown_class(cls):
        """oclint creates a plist file in the same directory, so remove that
            -> See https://github.com/oclint/oclint/issues/537"""
        if os.path.exists("test.plist"):
            os.remove("test.plist")
