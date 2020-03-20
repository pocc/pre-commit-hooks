#!/usr/bin/env python3
"""Tests clang-format, clang-tidy, and oclint against .c and .cpp
With this snippet:

    int main() {  int i;  return 10;}

- Triggers clang-format because what should be on 4 lines is on 1
- Triggers clang-tidy because "magical number" 10 is used
- Triggers oclint because short variable name is used

pytest_generate_tests comes from pytest documentation and allows for
table tests to be generated and each treated as a test by pytest.
This allows for 24 tests with a descrition instead of 3 which
functionally tests the same thing.
"""
import os
import subprocess as sp

import pytest

from hooks.clang_format import ClangFormatCmd
from hooks.clang_tidy import ClangTidyCmd
from hooks.oclint import OCLintCmd


def pytest_generate_tests(metafunc):
    """Taken from pytest documentation to allow for table tests:
    https://docs.pytest.org/en/latest/example/parametrize.html#paramexamples"""
    metafunc.cls.setup_class()
    idlist = []
    argvalues = []
    argnames = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append([x[1] for x in items])
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")


def generate_list_tests():
    """Generate the scenarios for class (24)

    Test looks like ["""
    pwd = os.getcwd()
    err_c = os.path.join(pwd, "tests/files/err.c")
    err_cpp = os.path.join(pwd, "tests/files/err.cpp")
    ok_c = os.path.join(pwd, "tests/files/ok.c")
    ok_cpp = os.path.join(pwd, "tests/files/ok.cpp")

    ok_str = ""

    clang_format_args_sets = [[], ["-i"]]
    clang_format_err = """\n<  int main() { int i; return 10; }\n---\n>  int main() {\n>    int i;\n>    return 10;\n>  }\n"""  # noqa: E501
    clang_format_output = [ok_str, ok_str, clang_format_err, clang_format_err]

    base_args = ["-quiet", "-checks=*", "-warnings-as-errors=*"]
    # Run normal, plus two in-place arguments
    additional_args = [[], ["-fix"], ["--fix-errors"]]
    clang_tidy_args_sets = [base_args + arg for arg in additional_args]
    clang_tidy_err_str = """{}:1:28: error: 10 is a magic number; consider replacing it with a named constant [cppcoreguidelines-avoid-magic-numbers,-warnings-as-errors]\nint main() {{ int i; return 10; }}\n                           ^\n"""  # noqa: E501
    clang_tidy_str_c = clang_tidy_err_str.format(err_c)
    clang_tidy_str_cpp = clang_tidy_err_str.format(err_cpp)
    clang_tidy_output = [ok_str, ok_str, clang_tidy_str_c, clang_tidy_str_cpp]

    oclint_arg_sets = [["-enable-global-analysis", "-enable-clang-static-analyzer"]]
    oclint_err_str = """Problem with oclint: OCLint Violations found\n\n\nOCLint Report\n\nSummary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2 \n
{0}:1:14: short variable name [naming|P3] Length of variable name `i` is 1, which is shorter than the threshold of 3
{0}:1:14: unused local variable [unused|P3] The local variable 'i' is unused.\n\n[OCLint (http://oclint.org) v0.13]\n\n"""  # noqa: E501

    oclint_err_str_c = oclint_err_str.format(err_c)
    oclint_err_str_cpp = oclint_err_str.format(err_cpp)
    oclint_output = [ok_str, ok_str, oclint_err_str_c, oclint_err_str_cpp]

    files = [ok_c, ok_cpp, err_c, err_cpp]
    retcodes = [0, 0, 1, 1]
    scenarios = []
    for i in range(len(files)):
        for arg_set in clang_format_args_sets:
            clang_format_scenario = [ClangFormatCmd, arg_set, files[i],
                                     clang_format_output[i], retcodes[i]]
            scenarios += [clang_format_scenario]
        for arg_set in clang_tidy_args_sets:
            clang_tidy_scenario = [ClangTidyCmd, arg_set, files[i],
                                   clang_tidy_output[i], retcodes[i]]
            scenarios += [clang_tidy_scenario]
        for arg_set in oclint_arg_sets:
            oclint_scenario = [OCLintCmd, arg_set, files[i],
                               oclint_output[i], retcodes[i]]
            scenarios += [oclint_scenario]
    return scenarios


class TestHooks:
    """Test all C Linters: clang-format, clang-tidy, and oclint."""
    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests."""
        scenarios = generate_list_tests()
        cls.scenarios = []
        for test_type in [cls.run_cmd_class, cls.run_shell_cmd]:
            for scenario in scenarios:
                desc = test_type.__name__ + " " + scenario[0].command + " on " + scenario[2]
                test_scenario = [
                    desc,
                    {
                        'test_type': test_type,
                        'cmd': scenario[0],
                        'args': scenario[1],
                        'filename': scenario[2],
                        'expected_output': scenario[3],
                        'expected_retcode': scenario[4]
                    }
                ]
                cls.scenarios += [test_scenario]

    def test_run(self, test_type, cmd, args, filename, expected_output, expected_retcode):
        """Test each command's class from its python file
        and the command for each generated by setup.py."""
        test_type_name = test_type.__name__
        print("Testing file", filename, "with class", cmd.command, "with test type", test_type_name)
        test_type(cmd, args, filename, expected_output, expected_retcode)
        self.revert_files_changed(args, filename)

    @staticmethod
    def revert_files_changed(args, filename):
        """Revert file changes made by this test to error files."""
        # Fix options don't overlap between utilities
        fix_inplace = "-fix" in args or "--fix-errors" in args or "-i" in args
        if fix_inplace and "err.c" in filename:
            sp.run(["git", "checkout", "tests/files"])

    @staticmethod
    def run_cmd_class(cmd_class, args, fname, target_output, target_retcode):
        """Test the command class in each python hook file"""
        cmd = cmd_class([fname] + args)
        if target_retcode == 0:
            cmd.run()
        else:
            with pytest.raises(SystemExit):
                cmd.run()
        actual = cmd.stdout + cmd.stderr
        retcode = cmd.returncode
        assert actual == target_output
        assert retcode == target_retcode

    @staticmethod
    def run_shell_cmd(cmd_class, args, fname, target_output, target_retcode):
        """Use command generated by setup.py and installed by pip
        Ex. oclint => oclint-hook for the hook command"""
        all_args = [cmd_class.command + "-hook", fname, *args]
        sp_child = sp.run(all_args, stdout=sp.PIPE, stderr=sp.PIPE)
        actual = str(sp_child.stdout + sp_child.stderr, encoding='utf-8')
        retcode = sp_child.returncode
        assert actual == target_output
        assert retcode == target_retcode

