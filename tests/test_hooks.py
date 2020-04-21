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
import re
import shutil
import subprocess as sp
import sys

import pytest

import tests.test_utils as utils
from hooks.clang_format import ClangFormatCmd
from hooks.clang_tidy import ClangTidyCmd
from hooks.cppcheck import CppcheckCmd
from hooks.oclint import OCLintCmd
from hooks.uncrustify import UncrustifyCmd


def compare_versions(expected_list, actual_versions, cmd_name):
    """Compare versions and alert if they don't match. Don't compare fix."""
    actl_maj, actl_min, actl_fix = actual_versions[cmd_name].split(".")[:3]
    for ver in expected_list:
        expd_maj, expd_min, expd_fix = ver.split(".")[:3]
        if expd_fix == actl_maj and expd_min == actl_min:
            return
    print("Unknown version ", actual_versions[cmd_name], " of", cmd_name)
    print("Known version:", expected_list)
    sys.exit(1)


def assert_command_versions(versions):
    """Raise an error if a new minor version of $cmd came out.
    Theses tests should work with command versions listed here."""
    # 7.0.0 on Ubuntu-16.04/18.04
    # 9.0.0 on Macos 10.13.6/brew
    clang_versions = ["6.0.0", "7.0.0", "8.0.0", "9.0.1"]
    compare_versions(clang_versions, versions, "clang-format")
    compare_versions(clang_versions, versions, "clang-tidy")

    if os.name != "nt":  # oclint does not target windows
        # 0.13.1, manually installed on Ubuntu-16.04/18.04
        # 0.15, manually installed on Ubuntu-16.04/18.0
        # 0.13.1 on Macos 10.13.6/brew
        oclint_versions = ["0.13.1", "0.15"]
        compare_versions(oclint_versions, versions, "oclint")

    # 0.59 on Ubuntu-16.04
    # 0.66.1_f on Ubuntu-18.04
    # 0.70.1_f on Macos 10.13.6/brew
    uncrustify_versions = ["0.59", "0.66.1_f", "0.70.1_f"]
    compare_versions(uncrustify_versions, versions, "uncrustify")

    # 1.72 on Ubuntu-16.04
    # 1.82 on Ubuntu-18.04
    # 1.89 on Macos 10.13.6/brew
    # 1.90 on Macos 10.14/brew
    cppcheck_versions = ["1.72", "1.82", "1.89", "1.90"]
    compare_versions(cppcheck_versions, versions, "cppcheck")


def set_compilation_db(filenames):
    """Create a compilation database for clang static analyzers."""
    cdb = "["
    clang_location = shutil.which("clang")
    file_dir = os.path.dirname(os.path.abspath(filenames[0]))
    for f in filenames:
        file_base = os.path.basename(f)
        clang_suffix = ""
        if f.endswith("cpp"):
            clang_suffix = "++"
        cdb += """\n{{
    "directory": "{0}",
    "command": "{1}{2} {3} -o {3}.o",
    "file": "{3}"
}},""".format(
            file_dir, clang_location, clang_suffix, os.path.join(file_dir, file_base)
        )
    cdb = cdb[:-1] + "]"  # Subtract extra comma and end json
    with open(file_dir + "/" + "compile_commands.json", "w") as f:
        f.write(cdb)


def get_multifile_scenarios(err_files, uncrustify_ver):
    """Create tests to verify that commands are handling both err.c/err.cpp as input correctly."""
    expected_err = """{}
====================
<  int main(){{int i;return;}}
---
>  int main(){}{{
>    int i;{}return;
>  }}
{}
====================
<  int main(){{int i;return;}}
---
>  int main(){}{{
>    int i;{}return;
>  }}
"""
    clangfmt_err = expected_err.format(err_files[0], " ", "\n>    ", err_files[1], " ", "\n>    ")
    uncrustify_err = expected_err.format(err_files[0], "", " ", err_files[1], "", " ")
    scenarios = [
        [ClangFormatCmd, ["--style=google"], err_files, clangfmt_err, 1],
        [UncrustifyCmd, [], err_files, uncrustify_err, 1],
    ]
    return scenarios


def generate_list_tests():
    """Generate the scenarios for class (45)

    This is all the arg (6) and file (4) combinations
    +2x tests:
        * Call the shell hooks installed with pip to mimic end user use
        * Call via importing the command classes to verify expectations"""
    versions = utils.get_versions()

    pwd = os.getcwd()
    err_c = os.path.join(pwd, "tests/files/err.c")
    err_cpp = os.path.join(pwd, "tests/files/err.cpp")
    ok_c = os.path.join(pwd, "tests/files/ok.c")
    ok_cpp = os.path.join(pwd, "tests/files/ok.cpp")

    ok_str = ""

    clang_format_args_sets = [["--style=google"], ["--style=google", "-i"]]
    clang_format_err = """{}
{}
<  int main(){{int i;return;}}
---
>  int main() {{
>    int i;
>    return;
>  }}
"""  # noqa: E501
    cf_c_err = clang_format_err.format(err_c, 20 * "=")
    cf_cpp_err = clang_format_err.format(err_cpp, 20 * "=")
    clang_format_output = [ok_str, ok_str, cf_c_err, cf_cpp_err]

    ct_base_args = ["-quiet", "-checks=clang-diagnostic-return-type"]
    # Run normal, plus two in-place arguments
    additional_args = [[], ["-fix"], ["--fix-errors"]]
    clang_tidy_args_sets = [ct_base_args + arg for arg in additional_args]
    clang_tidy_err_str = """{0}:1:18: error: non-void function 'main' should return a value [clang-diagnostic-return-type]
int main(){{int i;return;}}
                 ^
1 error generated.
Error while processing {0}.
"""  # noqa: E501
    clang_tidy_str_c = clang_tidy_err_str.format(err_c, "")
    clang_tidy_str_cpp = clang_tidy_err_str.format(err_cpp)
    clang_tidy_output = [ok_str, ok_str, clang_tidy_str_c, clang_tidy_str_cpp]

    # Specify config file as autogenerated one varies between uncrustify verions.
    # v0.66 on ubuntu creates an invalid config; v0.68 on osx does not.
    unc_base_args = ["-c", "tests/uncrustify_defaults.cfg"]
    unc_addtnl_args = [[], ["--replace", "--no-backup"]]
    uncrustify_arg_sets = [unc_base_args + arg for arg in unc_addtnl_args]
    unc_err = """{}\n====================\n<  int main(){{int i;return;}}\n---\n>  int main(){{\n>    int i; return;\n>  }}\n"""  # noqa: E501
    uncrustify_output = [ok_str, ok_str, unc_err.format(err_c), unc_err.format(err_cpp)]

    cppcheck_arg_sets = [[]]
    # cppcheck adds unnecessary error information.
    # See https://stackoverflow.com/questions/6986033
    cppc_ok = ""
    if versions["cppcheck"] <= "1.88":
        cppcheck_err = "[{}:1]: (style) Unused variable: i\n"
    # They've made changes to messaging
    elif versions["cppcheck"] >= "1.89":
        cppcheck_err = """{}:1:16: style: Unused variable: i [unusedVariable]
int main(){{int i;return;}}
               ^
"""
    else:
        print("Problem parsing version for cppcheck", versions["cppcheck"])
        print("Please create an issue on github.com/pocc/pre-commit-hooks")
        cppcheck_err = ""
    cppcheck_err_c = cppcheck_err.format(err_c)
    cppcheck_err_cpp = cppcheck_err.format(err_cpp)
    cppcheck_output = [cppc_ok, cppc_ok, cppcheck_err_c, cppcheck_err_cpp]

    files = [ok_c, ok_cpp, err_c, err_cpp]
    retcodes = [0, 0, 1, 1]
    scenarios = []
    for i in range(len(files)):
        for arg_set in clang_format_args_sets:
            clang_format_scenario = [ClangFormatCmd, arg_set, [files[i]], clang_format_output[i], retcodes[i]]
            scenarios += [clang_format_scenario]
        for arg_set in clang_tidy_args_sets:
            clang_tidy_scenario = [ClangTidyCmd, arg_set, [files[i]], clang_tidy_output[i], retcodes[i]]
            scenarios += [clang_tidy_scenario]
        for arg_set in uncrustify_arg_sets:
            uncrustify_scenario = [UncrustifyCmd, arg_set, [files[i]], uncrustify_output[i], retcodes[i]]
            scenarios += [uncrustify_scenario]
        for arg_set in cppcheck_arg_sets:
            cppcheck_scenario = [CppcheckCmd, arg_set, [files[i]], cppcheck_output[i], retcodes[i]]
            scenarios += [cppcheck_scenario]
    if os.name != "nt":
        oclint_err = """
Compiler Errors:
(please be aware that these errors will prevent OCLint from analyzing this source code)

{0}:1:18: non-void function 'main' should return a value

Clang Static Analyzer Results:

{0}:1:18: non-void function 'main' should return a value


OCLint Report

Summary: TotalFiles=0 FilesWithViolations=0 P1=0 P2=0 P3=0{1}


[OCLint (http://oclint.org) v{2}]
"""
        oclint_arg_sets = [["-enable-global-analysis", "-enable-clang-static-analyzer"]]
        ver_output = sp.check_output(["oclint", "--version"]).decode("utf-8")
        oclint_ver = re.search(r"OCLint version ([\d.]+)\.", ver_output).group(1)
        eol_whitespace = " "
        oclint_err_str_c = oclint_err.format(err_c, eol_whitespace, oclint_ver)
        oclint_err_str_cpp = oclint_err.format(err_cpp, eol_whitespace, oclint_ver)
        oclint_output = [ok_str, ok_str, oclint_err_str_c, oclint_err_str_cpp]
        for i in range(len(files)):
            for arg_set in oclint_arg_sets:
                oclint_scenario = [OCLintCmd, arg_set, [files[i]], oclint_output[i], retcodes[i]]
                scenarios += [oclint_scenario]

    scenarios += get_multifile_scenarios([err_c, err_cpp], versions["uncrustify"])

    return scenarios


class TestHooks:
    """Test all C Linters: clang-format, clang-tidy, and oclint."""

    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests."""
        os.makedirs("tests/files/temp", exist_ok=True)
        scenarios = generate_list_tests()
        filenames = ["tests/files/" + f for f in ["ok.c", "ok.cpp", "err.c", "err.cpp"]]
        set_compilation_db(filenames)
        cls.scenarios = []
        for test_type in [cls.run_cmd_class, cls.run_shell_cmd]:
            for s in scenarios:
                type_name = test_type.__name__
                desc = " ".join([type_name, s[0].command, " ".join(s[2]), " ".join(s[1])])
                test_scenario = [
                    desc,
                    {
                        "test_type": test_type,
                        "cmd": s[0],
                        "args": s[1],
                        "files": s[2],
                        "expd_output": s[3],
                        "expd_retcode": s[4],
                    },
                ]
                cls.scenarios += [test_scenario]

    @staticmethod
    def determine_edit_in_place(cmd_name, args):
        """runtime means to check if cmd/args will edit files"""
        retval = (
            cmd_name == "clang-format"
            and "-i" in args
            or cmd_name == "clang-tidy"
            and ("-fix" in args or "--fix-errors" in args)
            or cmd_name == "uncrustify"
            and "--replace" in args
        )
        return retval

    def test_run(self, test_type, cmd, args, files, expd_output, expd_retcode):
        """Test each command's class from its python file
        and the command for each generated by setup.py."""
        fix_in_place = self.determine_edit_in_place(cmd.command, args)
        has_err_file = any(["err.c" in f for f in files])
        use_temp_files = fix_in_place and has_err_file
        if use_temp_files:
            temp_files = list()
            for f in files:
                temp_file = utils.create_temp_dir_for(f)
                expd_output = expd_output.replace(f, temp_file)
                temp_files.append(temp_file)
            files = temp_files
            set_compilation_db(files)
        test_type(cmd, args, files, expd_output, expd_retcode)
        if use_temp_files:
            for f in files:
                temp_dir = os.path.dirname(f)
                shutil.rmtree(temp_dir)

    @staticmethod
    def run_cmd_class(cmd_class, args, files, target_output, target_retcode):
        """Test the command class in each python hook file"""
        cmd = cmd_class(files + args)
        if target_retcode == 0:
            cmd.run()
        else:
            with pytest.raises(SystemExit):
                cmd.run()
                # If this continues with no system exit, print info
                print("stdout:`" + cmd.stdout + "`")
                print("stderr:`" + cmd.stderr + "`")
                print("returncode:", cmd.returncode)
        actual = cmd.stdout + cmd.stderr
        retcode = cmd.returncode
        utils.assert_equal(target_output, actual)
        assert target_retcode == retcode

    @staticmethod
    def run_shell_cmd(cmd_class, args, files, target_output, target_retcode):
        """Use command generated by setup.py and installed by pip
        Ex. oclint => oclint-hook for the hook command"""
        all_args = [cmd_class.command + "-hook", *files, *args]
        sp_child = sp.run(all_args, stdout=sp.PIPE, stderr=sp.PIPE)
        actual = str(sp_child.stdout + sp_child.stderr, encoding="utf-8")
        retcode = sp_child.returncode
        utils.assert_equal(target_output, actual)
        assert target_retcode == retcode

    @staticmethod
    def teardown_class():
        """Delete files generated by these tests."""
        generated_files = ["tests/files/" + f for f in ["ok.plist", "err.plist"]]
        for filename in generated_files:
            if os.path.exists(filename):
                os.remove(filename)
