#!/usr/bin/env python3
"""Tests clang-format, clang-tidy, and oclint against .c and .cpp
With this snippet:

    int main() {  int i;  return 10;}

- Triggers clang-format because what should be on 4 lines is on 1
- Triggers clang-tidy because "magical number" 10 is used
- Triggers oclint because short variable name is used

pytest_generate_tests comes from pytest documentation and allows for
table tests to be generated and each treated as a test by pytest.
This allows for 45 tests with a descrition instead of 3 which
functionally tests the same thing.
"""
import os
import shutil
import subprocess as sp
import uuid

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


def create_temp_dir_for(filename):
    """Create a temporary dir for a file, returning the file path."""
    uuid_dir = str(uuid.uuid4())
    temp_dir = os.path.join("tests/files/temp", uuid_dir)
    os.makedirs(temp_dir)
    new_temp_name = shutil.copy2(filename, temp_dir)
    return os.path.join(os.getcwd(), new_temp_name)


def generate_list_tests():
    """Generate the scenarios for class (45)

    This is all the arg (6) and file (4) combinations
    +2x tests:
        * Call the shell hooks installed with pip to mimic end user use
        * Call via importing the command classes to verify expectations"""
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

    oclint_arg_sets = [
        ["-enable-global-analysis", "-enable-clang-static-analyzer"]
    ]
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
            clang_format_scenario = [
                ClangFormatCmd,
                arg_set,
                files[i],
                clang_format_output[i],
                retcodes[i],
            ]
            scenarios += [clang_format_scenario]
        for arg_set in clang_tidy_args_sets:
            clang_tidy_scenario = [
                ClangTidyCmd,
                arg_set,
                files[i],
                clang_tidy_output[i],
                retcodes[i],
            ]
            scenarios += [clang_tidy_scenario]
        for arg_set in oclint_arg_sets:
            oclint_scenario = [
                OCLintCmd,
                arg_set,
                files[i],
                oclint_output[i],
                retcodes[i],
            ]
            scenarios += [oclint_scenario]
    return scenarios


class TestHooks:
    """Test all C Linters: clang-format, clang-tidy, and oclint."""

    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests."""
        os.makedirs("tests/files/temp", exist_ok=True)
        scenarios = generate_list_tests()
        cls.scenarios = []
        for test_type in [cls.run_cmd_class, cls.run_shell_cmd]:
            for s in scenarios:
                type_name = test_type.__name__
                name_list = [type_name, s[0].command, str(s[1]), s[2]]
                desc = "{} {} {} on {}".format(*name_list)
                test_scenario = [
                    desc,
                    {
                        "test_type": test_type,
                        "cmd": s[0],
                        "args": s[1],
                        "fname": s[2],
                        "expd_output": s[3],
                        "expd_retcode": s[4],
                    },
                ]
                cls.scenarios += [test_scenario]

    def test_run(self, test_type, cmd, args, fname, expd_output, expd_retcode):
        """Test each command's class from its python file
        and the command for each generated by setup.py."""
        fix_in_place = "-i" in args or "-fix" in args or "--fix-errors" in args
        if fix_in_place and "err.c" in fname:
            temp_file = create_temp_dir_for(fname)
            expd_output = expd_output.replace(fname, temp_file)
            fname = temp_file
        test_type(cmd, args, fname, expd_output, expd_retcode)
        if fix_in_place and "err.c" in fname:
            temp_dir = os.path.dirname(fname)
            shutil.rmtree(temp_dir)

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
        actual = str(sp_child.stdout + sp_child.stderr, encoding="utf-8")
        retcode = sp_child.returncode
        assert actual == target_output
        assert retcode == target_retcode
