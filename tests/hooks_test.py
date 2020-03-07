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

from hooks.clangformat import ClangFormatCmd
from hooks.clangtidy import ClangTidyCmd
from hooks.oclint import OCLintCmd


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
        clang_format_err = r"""
<  int main() { int i; return 10; }
---
>  int main() {
>    int i;
>    return 10;
>  }
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
        error_version = "0.0.0"

        clang_version_err = """\
Problem with clang-format: Version of clang-format is wrong
Expected version is {} but actual system version is {}.
Edit your pre-commit config or use a\
 different version of clang-format""".format(
            error_version, cf_version
        )
        self.run_clang_format(
            filelist=self.okfiles,
            expected_output=clang_version_err,
            expected_retcode=1,
            version=error_version,
        )

    @staticmethod
    def run_clang_format(
        filelist, expected_output, expected_retcode, version=""
    ):
        """Test that oclint returns correct retcode & output for files.

        Use google style, printing a format diff to stdout."""
        args = []
        if version:
            args += ["--version", version]
        for filename in filelist:
            print("\nAnalyzing file", filename)
            cmd = ClangFormatCmd([filename] + args)
            if version and cmd.retcode != 0:
                actual = cmd.stderr
            else:
                cmd.run()
                actual = cmd.stdout + cmd.stderr
            retcode = cmd.retcode
            # Expecting error text with a err return code
            assert actual == expected_output
            assert retcode == expected_retcode

    def test_clang_tidy_ok(self):
        self.run_clang_tidy(
            filelist=self.okfiles, expected_output="", expected_retcode=0
        )

    def test_clang_tidy_err(self):
        clang_tidy_error = """Problem with clang-tidy: On running command with \
args, -quiet -checks=* -warnings-as-errors=* -- \
-DCMAKE_EXPORT_COMPILE_COMMANDS=ON

Return code:1

STDOUT:
/Users/rj/code/pre-commit-hooks/tests/files/err.c{}:1:28: error: 10 is a \
magic number; consider replacing it with a named constant \
[cppcoreguidelines-avoid-magic-numbers,-warnings-as-errors]
int main() {{ int i; return 10; }}
                           ^

STDERR:"""
        clang_tidy_error1 = clang_tidy_error.format("")
        clang_tidy_error2 = clang_tidy_error.format("pp")
        # noqa: E501
        self.run_clang_tidy(
            filelist=[self.errfiles[0]],
            expected_output=clang_tidy_error1,
            expected_retcode=1,
        )
        self.run_clang_tidy(
            filelist=[self.errfiles[1]],
            expected_output=clang_tidy_error2,
            expected_retcode=1,
        )

    def test_clang_tidy_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["clang-tidy", "--version"], text=True)
        ct_version = re.search(r"LLVM version ([\S]+)", output).group(1)
        error_version = "0.0.0"

        clang_version_err = r"""Problem with clang-tidy: Version of clang-tidy is wrong
Expected version is {} but actual system version is {}.
Edit your pre-commit config or use a different version of clang-tidy""".format(
            error_version, ct_version
        )
        self.run_clang_tidy(
            filelist=self.okfiles,
            expected_output=clang_version_err,
            expected_retcode=1,
            version=error_version,
        )

    @pytest.mark.slow
    def run_clang_tidy(
        self, filelist, expected_output, expected_retcode, version=""
    ):
        """Test that clang tidy returns correct retcode & output for files."""
        args = ["-quiet", "-checks=*", "-warnings-as-errors=*"]
        if version:
            args += ["--version", version]
        for filename in filelist:
            print("\nAnalyzing file", filename)
            cmd = ClangTidyCmd([filename] + args)
            # Version docstring doesn't contain a {0}
            if version and cmd.retcode != 0:
                actual = cmd.stderr
            else:
                cmd.run()
                # If stdout exists, it's formatted in stderr due to clang-tidy
                # switching stdout/stderr (see parsing comment in file)
                actual = cmd.stdout + cmd.stderr
            retcode = cmd.retcode
            assert actual == expected_output
            assert retcode == expected_retcode

    @pytest.mark.slow
    def test_oclint_ok(self):
        expected_output = """\n\nOCLint Report\n
Summary: TotalFiles=1 FilesWithViolations=0 P1=0 P2=0 P3=0 \n\n
[OCLint (http://oclint.org) v0.13]\n"""
        self.run_oclint(self.okfiles, expected_output, expected_retcode=0)

    @pytest.mark.slow
    def test_oclint_err(self):
        oclint_stdout_err = r"""

OCLint Report

Summary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2{0}

{1}:1:14: short variable name [naming|P3] Length of variable name `i` is 1, which is shorter than the threshold of 3
{1}:1:14: unused local variable [unused|P3] The local variable 'i' is unused.

[OCLint (http://oclint.org) v0.13]
Problem with oclint: OCLint Violations found
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
        oclint_ver = re.search(r"OCLint version ([\d.]+)", output).group(1)

        clang_version_err = r"""Problem with oclint: Version of oclint is wrong
Expected version is 0.0.0 but actual system version is {}.
Edit your pre-commit config or use a different version of oclint""".format(
            oclint_ver
        )
        self.run_oclint(
            filelist=self.okfiles,
            expected_output=clang_version_err,
            expected_retcode=1,
            version="0.0.0",
        )

    @staticmethod
    def run_oclint(filelist, expected_output, expected_retcode, version=""):
        """Test that oclint returns correct retcode & output for files."""
        args = ["-enable-global-analysis", "-enable-clang-static-analyzer"]
        if version:
            args += ["--version", version]
        for filename in filelist:
            print("\nAnalyzing file", filename)
            # Version docstring doesn't contain a {0} (see above docstring)
            if version:
                expected = expected_output
            else:
                expected = expected_output.format(filename)
            cmd = OCLintCmd([filename] + args)
            if version and cmd.retcode != 0:
                actual = cmd.stderr
            else:
                cmd.run()
                actual = cmd.stdout + cmd.stderr
            retcode = cmd.retcode
            # Expecting error text with a err return code
            assert actual == expected
            assert retcode == expected_retcode

    @classmethod
    def teardown_class(cls):
        """oclint creates a plist file in the same directory, so remove that
            -> See https://github.com/oclint/oclint/issues/537"""
        if os.path.exists("test.plist"):
            os.remove("test.plist")
