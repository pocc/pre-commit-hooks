#!/usr/bin/env python
"""Test that --version works for each hook correctly"""
import re
import subprocess as sp

from hooks.clang_format import ClangFormatCmd
from hooks.clang_tidy import ClangTidyCmd
from hooks.oclint import OCLintCmd
from hooks.uncrustify import UncrustifyCmd


class TestVersions:
    """Test the --version flag for hooks: clang-format, clang-tidy, and oclint."""

    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests"""
        cls.err_str = """Problem with {0}: Version of {0} is wrong
Expected version: {1}
Found version: {2}
Edit your pre-commit config or use a different version of {0}.
"""
        cls.err_ver = "0.0.0"

    def test_clang_format_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["clang-format", "--version"]).decode("utf-8")
        actual_ver = re.search(r"version ([\S]+)", output).group(1)
        self.run_table_tests(ClangFormatCmd, actual_ver)

    def test_clang_tidy_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["clang-tidy", "--version"]).decode("utf-8")
        actual_ver = re.search(r"LLVM version ([\S]+)", output).group(1)
        self.run_table_tests(ClangTidyCmd, actual_ver)

    def test_oclint_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["oclint", "--version"]).decode("utf-8")
        actual_ver = re.search(r"OCLint version ([\d.]+)", output).group(1)
        self.run_table_tests(OCLintCmd, actual_ver)

    def test_uncrustify_version_err(self):
        """Check that --version=0 errors."""
        output = sp.check_output(["uncrustify", "--version"]).decode("utf-8")
        actual_ver = re.search(r"Uncrustify-([\d._a-z]+)", output).group(1)
        self.run_table_tests(UncrustifyCmd, actual_ver)

    def run_table_tests(self, cmd, actual_ver):
        err_str = self.err_str.format(cmd.command, self.err_ver, actual_ver)
        # Removing last char ~= having actual version be $ver-beta or $ver.5
        fuzzy_version = actual_ver[:-1]

        table_tests = [
            [actual_ver, "", 0],
            [fuzzy_version, "", 0],
            [self.err_ver, err_str, 1],
        ]
        for t in table_tests:
            self.check_version(cmd, *t)

    @staticmethod
    def check_version(cmd_class, version, expected_stderr, expected_retcode):
        args = [cmd_class.command + "-hook", "--version", version]
        sp_child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        actual_stderr = str(sp_child.stderr, encoding="utf-8")
        actual_retcode = sp_child.returncode
        assert actual_stderr == expected_stderr
        assert actual_retcode == expected_retcode
