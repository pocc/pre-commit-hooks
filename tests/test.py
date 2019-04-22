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
import unittest


class TestCLinters(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        testfiles = ["test.c", "test.cpp"]
        c_program = "int main() { int i; return 10; }"
        for filename in testfiles:
            with open(filename, 'w') as f:
                f.write(c_program)
        cls.testfiles = [os.path.abspath(filename) for filename in testfiles] 

    def test_clang_format(self):
        """Test clang format using google style, printing to stdout."""
        expected = 'int main() {\n  int i;\n  return 10;\n}'
        for filename in self.testfiles:
            actual = sp.check_output(["hooks/clang-format", filename], text=True)
            assert actual == expected

    def test_clang_tidy(self):
        """Test clang tidy using all checks."""
        clang_tidy_expected = """\
2 warnings generated.
{0}:1:28: error: 10 is a magic number; consider replacing it with a named constant [cppcoreguidelines-avoid-magic-numbers,-warnings-as-errors]
int main() {{ int i; return 10; }}
                           ^
"""
        cmds = ["./hooks/clang-tidy", "-quiet", "-checks=*", "-warnings-as-errors=*"]
        for filename in self.testfiles:
            expected = clang_tidy_expected.format(filename)
            actual = self.get_all_output(cmds, filename)
            # In case num warnings changes due to more checks
            actual = re.sub(r"^\d+", "2", actual)
            assert actual == expected 
 
    def test_oclint(self):
        """Test oclint with major analyses turned on."""
        oclint_expected_template = """\


OCLint Report

Summary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2 

{0}:1:14: short variable name [naming|P3] Length of variable name `i` is 1, which is shorter than the threshold of 3
{0}:1:14: unused local variable [unused|P3] The local variable 'i' is unused.

[OCLint (http://oclint.org) v0.13]
"""
        cmds = ["./hooks/oclint", "-enable-global-analysis",
                "-enable-clang-static-analyzer"]
        for filename in self.testfiles:
            expected = oclint_expected_template.format(filename)
            actual = self.get_all_output(cmds, filename)
            assert actual == expected

    @staticmethod
    def get_all_output(cmds, filename):
        """Helper fn to get stderr and stdout from llvm command.
        
        Args:
            cmds (list): List of commands to send to Popen
            filename (str): Name of file to run commands against
        Returns (str):
            Text output of function
        """
        combined_cmds = cmds + [filename]
        _pipe = sp.Popen(combined_cmds, stderr=sp.STDOUT, stdout=sp.PIPE)
        return _pipe.communicate()[0].decode('utf-8')

    @classmethod
    def teardown_class(cls):
        """oclint creates a plist file in the same directory, so remove that
            -> See https://github.com/oclint/oclint/issues/537"""
        if os.path.exists("test.plist"):
            os.remove("test.plist")
        for filename in cls.testfiles:
            os.remove(filename)
