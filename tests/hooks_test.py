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

    def test_clang_format_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["clang-format", "--version"], text=True)
        cf_version = re.search(r"version ([\S]+)", output).group(1)

        clang_version_err = r"""ERR: Expected version 0.0.0, but system version is {}
Edit your pre-commit config or use a different version of clang-format
""".format(
            cf_version
        )
        self.run_clang_format(
            filelist=self.okfiles,
            expected_output=clang_version_err,
            expected_retcode=1,
            version="0.0.0",
        )

    @staticmethod
    def run_clang_format(filelist, expected_output, expected_retcode, version=""):
        """Test that oclint returns correct retcode & output for files.

        Use google style, printing a format diff to stdout."""
        for filename in filelist:
            print("Analyzing file", filename)
            cmds = ["hooks/clang-format", filename]
            if version:
                cmds += ["--version=" + version]
            _pipe = sp.Popen(cmds, text=True, stdout=sp.PIPE, stderr=sp.STDOUT)
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

    def test_clang_tidy_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["clang-tidy", "--version"], text=True)
        ct_version = re.search(r"version ([\S]+)", output).group(1)

        clang_version_err = r"""ERR: Expected version 0.0.0, but system version is {}
Edit your pre-commit config or use a different version of clang-tidy
""".format(
            ct_version
        )
        self.run_clang_tidy(
            filelist=self.okfiles,
            expected_output=clang_version_err,
            expected_retcode=1,
            version="0.0.0",
        )

    def run_clang_tidy(self, filelist, expected_output, expected_retcode, version=""):
        """Test that clang tidy returns correct retcode & output for files."""
        cmds = [
            "./hooks/clang-tidy",
            "-quiet",
            "-checks=*",
            "-warnings-as-errors=*",
        ]
        if version:
            cmds += ["--version=" + version]
        for filename in filelist:
            if version:  # Version docstring doesn't contain a {0}
                expected = expected_output
            else:
                expected = expected_output.format(filename)
            # In case num warnings changes due to more checks
            actual, retcode = self.get_all_output(cmds, filename)
            actual = re.sub(r"^\d+", "2", actual)
            # Expecting error text with a err return code
            assert actual == expected
            assert retcode == expected_retcode

    @pytest.mark.slow
    def test_oclint_ok(self):
        self.run_oclint(filelist=self.okfiles, expected_output="", expected_retcode=0)

    @pytest.mark.slow
    def test_oclint_err(self):
        oclint_stdout_err = r"""

OCLint Report

Summary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2{0}

{1}:1:14: short variable name [naming|P3] Length of variable name `i` is 1, which is shorter than the threshold of 3
{1}:1:14: unused local variable [unused|P3] The local variable 'i' is unused.

[OCLint (http://oclint.org) v0.13]
"""  # noqa: E501
        # Add extra space to end of line so linters don't complain/autofix
        oclint_stdout_err = oclint_stdout_err.format(" ", "{0}")
        self.run_oclint(
            filelist=self.errfiles,
            expected_output=oclint_stdout_err,
            expected_retcode=1,
        )

    @pytest.mark.slow
    def test_oclint_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["oclint", "--version"], text=True)
        oclint_ver = re.search(r"OCLint version ([\S]+)\.", output).group(1)

        clang_version_err = r"""ERR: Expected version 0.0.0, but system version is {}
Edit your pre-commit config or use a different version of oclint
""".format(
            oclint_ver
        )
        self.run_oclint(
            filelist=self.okfiles,
            expected_output=clang_version_err,
            expected_retcode=1,
            version="0.0.0",
        )

    def run_oclint(self, filelist, expected_output, expected_retcode, version=""):
        """Test that oclint returns correct retcode & output for files."""
        cmds = [
            "./hooks/oclint",
            "-enable-global-analysis",
            "-enable-clang-static-analyzer",
        ]
        if version:
            cmds += ["--version=" + version]
        for filename in filelist:
            print("Analyzing file", filename)
            if version:  # Version docstring doesn't contain a {0}
                expected = expected_output
            else:
                expected = expected_output.format(filename)
            print(" ".join(cmds))
            actual, retcode = self.get_all_output(cmds, filename)
            # Expecting error text with a err return code
            assert actual == expected
            assert retcode == expected_retcode

    @staticmethod
    def test_sticky_version_minor():
        """Verify that 6.0 matches minor versions like 6.0.1."""
        cmds = ["bash", "-c", ". ./hooks/utils; assert_version '{}' '6.0'"]
        cmds[2] = cmds[2].format("6.0.1")
        child = sp.Popen(cmds, stdout=sp.PIPE, stderr=sp.PIPE)
        child_out, child_err = child.communicate()
        assert child_out == b""
        assert child_err == b""
        assert child.returncode == 0

    @staticmethod
    def test_sticky_version_extended():
        cmds = ["bash", "-c", ". ./hooks/utils; assert_version '{}' '6.0'"]
        cmds[2] = cmds[2].format("6.0.0-1ubuntu2")
        child = sp.Popen(cmds, stdout=sp.PIPE, stderr=sp.PIPE)
        child_out, child_err = child.communicate()
        assert child_out == b""
        assert child_err == b""
        assert child.returncode == 0

    @staticmethod
    def test_sticky_version_err():
        cmds = ["bash", "-c", ". ./hooks/utils; assert_version '{}' '6.0'"]
        cmds[2] = cmds[2].format("6.1.0")
        child = sp.Popen(cmds, stdout=sp.PIPE, stderr=sp.PIPE)
        child_out, child_err = child.communicate()
        print(child_err)
        assert child_out == b""
        assert (
            child_err
            == b"ERR: Expected version 6.0, but system version is 6.1.0\n"
            + b"Edit your pre-commit config or use a different version of \n"
        )
        assert child.returncode == 1

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
        _pipe = sp.Popen(combined_cmds, stderr=sp.STDOUT, stdout=sp.PIPE, text=True)
        retvals = _pipe.communicate()[0], _pipe.returncode
        return retvals

    @classmethod
    def teardown_class(cls):
        """oclint creates a plist file in the same directory, so remove that
            -> See https://github.com/oclint/oclint/issues/537"""
        if os.path.exists("test.plist"):
            os.remove("test.plist")
