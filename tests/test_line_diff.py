#!/bin/bash/env python3
"""Test clang-format clang-tidy oclint cppcheck cpplint
with only the lines changed in the last commit.

Do not support/test uncrustify nor iwyu because they doesn't support line numbers"""
import subprocess as sp
import re
from typing import List, Type, Union

import tests.test_utils as utils
from hooks.line_diff import parse_diff_lines
from hooks.clang_tidy import ClangTidyCmd
from hooks.cppcheck import CppcheckCmd
from hooks.cpplint import CpplintCmd


GIT_DIFF = """\
diff --git a/err.cpp b/err.cpp
index c836637..1b29977 100644
--- a/err.cpp
+++ b/err.cpp
@@ -0,0 +1,2 @@
+#include <string>
+int main(){int i;return;}
@@ -1,0 +4 @@
+int third(){int i;return;}"""

ERR_CPP_STR = """\
#include <string>
int main(){int i;return;}
int second(){int i;return;}
int third(){int i;return;}"""

# lines are 1-2, 4, so formatters don't touch lines
partial_output_cpp_str = """\
#include <string>
int main() {
  int i;
  return;
}
int second(){int i;return;}
int third() {
  int i;
  return;
}"""

commented_code = """\
class TestLineDiff:
    @classmethod
    def setup_class(cls):
        cls.scenarios = [
            [
                "Line diff test",
                {
                    "num": 0,
                },
            ]
        ]

    def test_run(cls, num):
        ""If -p is in arguments make sure -DCMAKE_EXPORT_COMPILE_COMMANDS is *not*""
        print(num)
        cls.t3st_parse_diff_lines()
        cls.t3st_formatter_diff("clang-format")
        cls.t3st_formatter_diff("uncrustify")

    @classmethod
    def teardown_class(cls):
        if os.path.exists('err.cpp'):
            os.remove('err.cpp')
"""

def t3st_parse_diff_lines():
    """Run tests against line diffs"""
    output = parse_diff_lines(GIT_DIFF)
    assert {'err.cpp': [[1, 2], [4, 1]]} == output

def t3st_formatter_diff(command: str):
    """Run tests against clang-format and uncrustify

    This will
    1. Get the lines in files that have changed since the last commit
    2. Apply the command + args to only the lines in those files
    3. Error if there's a difference in those lines
    """
    altered_err_cpp_str = ERR_CPP_STR
    uncrustify_f_flag = []
    if command == "uncrustify":
        uncrustify_f_flag = ["-f"]
    line_ranges = [[1, 2], [4, 1]]
    err_cpp_lines = ERR_CPP_STR.split('\n')
    for line_range in line_ranges:
        min_line = line_range[0] - 1
        max_line = line_range[0] + line_range[1] - 1
        # subtract one due to github diff's starting at 1, 2nd number is length
        content = '\n'.join(err_cpp_lines[min_line:max_line])
        with open('err.cpp', 'w') as f:
            f.write(content)
        commands = [command] + uncrustify_f_flag + ['err.cpp']
        child = sp.run(commands, stdout=sp.PIPE, stderr=sp.PIPE)
        altered_text = child.stdout.decode() + child.stderr.decode()
        altered_err_cpp_str = altered_err_cpp_str.replace(content, altered_text, 1)

    utils.assert_equal(partial_output_cpp_str.encode(), altered_err_cpp_str.encode())

StaticAnalyzerCmdType = Union[ClangTidyCmd, CppcheckCmd, CpplintCmd]

def t3st_static_analyzer_diff(Command: Type[StaticAnalyzerCmdType]):
    r"""Run tests against static analyzers clang-tidy oclint cppcheck cpplint

    iwyu_regex = r"\/\/ lines (\d+)-(\d+)"

    This will
    1. Get the lines in files that have changed since the last commit
    2. Apply the linter to all files that have changed
    3. Collect errors/warnings that match
    """
    # for clang-tidy, oclint, cppcheck, cpplint
    linter_regex = r"([^:\n]+):(\d+):"
    with open('tests/test_repo/err_lines.cpp', 'w') as f:
        f.write(ERR_CPP_STR)
    cmd = Command(args=[])
    cmd.files = ['tests/test_repo/err_lines.cpp']
    cmd.run()
    output = cmd.stdout + cmd.stderr
    line_ranges = [[1, 2], [4, 1]]
    matches = re.findall(linter_regex, output.decode())
    line_nums: List[int] = []
    for line_range in line_ranges:
        min_line = line_range[0]
        max_line = line_range[0] + line_range[1]
        for match in matches:
            if min_line <= int(match[1]) and int(match[1]) < max_line:
                line_nums.append(int(match[1]))
    print(cmd, line_nums)
    assert line_nums == [2, 4]

t3st_formatter_diff('clang-format')

t3st_static_analyzer_diff(ClangTidyCmd)
t3st_static_analyzer_diff(CppcheckCmd)
t3st_static_analyzer_diff(CpplintCmd)
