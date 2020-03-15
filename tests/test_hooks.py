#!/usr/bin/env python3
"""Tests clang-format, clang-tidy, and oclint against .c and .cpp
With this snippet:

    int main() {  int i;  return 10;}

- Triggers clang-format because what should be on 4 lines is on 1
- Triggers clang-tidy because "magical number" 10 is used
- Triggers oclint because short variable name is used
"""
import os

import pytest

from hooks.clangformat import ClangFormatCmd
from hooks.clangtidy import ClangTidyCmd
from hooks.oclint import OCLintCmd


class TestHooks:
    """Test all C Linters: clang-format, clang-tidy, and oclint."""
    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests.

        "err" files are expected to error for all linters
        "ok" files are expected to pass for all listers
        """
        pwd = os.getcwd()
        cls.err_c = os.path.join(pwd, "tests/files/err.c")
        cls.err_cpp = os.path.join(pwd, "tests/files/err.cpp")
        cls.ok_c = os.path.join(pwd, "tests/files/ok.c")
        cls.ok_cpp = os.path.join(pwd, "tests/files/ok.cpp")

    def run_table_tests(self, cmd, args, tests):
        for t in tests:
            self.run_command(cmd, args, *t)

    def test_clang_format(self):
        ok_str = ""
        err_str = """\n<  int main() { int i; return 10; }\n---\n>  int main() {\n>    int i;\n>    return 10;\n>  }\n"""  # noqa: E501
        cf_tests = [
            [self.ok_c, ok_str, 0],
            [self.ok_cpp, ok_str, 0],
            [self.err_c, err_str, 1],
            [self.err_cpp, err_str, 1],
        ]

        self.run_table_tests(ClangFormatCmd, [], cf_tests)

    def test_clang_tidy(self):
        ok_str = ""
        err_str = """Problem with clang-tidy: On running command with args, -quiet -checks=* -warnings-as-errors=* -- -DCMAKE_EXPORT_COMPILE_COMMANDS=ON\n\nReturn code:1\n\nSTDOUT:
{}:1:28: error: 10 is a magic number; consider replacing it with a named constant [cppcoreguidelines-avoid-magic-numbers,-warnings-as-errors]\nint main() {{ int i; return 10; }}\n                           ^\n\nSTDERR:"""  # noqa: E501
        err_str_c = err_str.format(self.err_c)
        err_str_cpp = err_str.format(self.err_cpp)
        ct_tests = [
            [self.ok_c, ok_str, 0],
            [self.ok_cpp, ok_str, 0],
            [self.err_c, err_str_c, 1],
            [self.err_cpp, err_str_cpp, 1],
        ]

        args = ["-quiet", "-checks=*", "-warnings-as-errors=*"]
        self.run_table_tests(ClangTidyCmd, args, ct_tests)

    @pytest.mark.slow
    def test_oclint_err(self):
        ok_str = """\n\nOCLint Report\n\nSummary: TotalFiles=1 FilesWithViolations=0 P1=0 P2=0 P3=0 \n\n\n[OCLint (http://oclint.org) v0.13]\n"""  # noqa: E501
        err_str = """\n\nOCLint Report\n\nSummary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2 \n
{0}:1:14: short variable name [naming|P3] Length of variable name `i` is 1, which is shorter than the threshold of 3
{0}:1:14: unused local variable [unused|P3] The local variable 'i' is unused.\n\n[OCLint (http://oclint.org) v0.13]\nProblem with oclint: OCLint Violations found\n"""  # noqa: E501
        err_str_c = err_str.format(self.err_c)
        err_str_cpp = err_str.format(self.err_cpp)
        ocl_tests = [
            [self.ok_c, ok_str, 0],
            [self.ok_cpp, ok_str, 0],
            [self.err_c, err_str_c, 1],
            [self.err_cpp, err_str_cpp, 1],
        ]

        args = ["-enable-global-analysis", "-enable-clang-static-analyzer"]
        self.run_table_tests(OCLintCmd, args, ocl_tests)

    @staticmethod
    def run_command(cmd_class, args, filename, expected_output, expected_retcode):
        print("\nAnalyzing file", filename)
        cmd = cmd_class([filename] + args)
        cmd.run()
        if cmd_class.command == "oclint":
            cmd.cleanup()  # Cleanup oclint-generated plist files
        actual = cmd.stdout + cmd.stderr
        retcode = cmd.retcode
        assert actual == expected_output
        assert retcode == expected_retcode

