#!/usr/bin/env python
"""Test that --version works for each hook correctly"""
import os
import subprocess as sp

import tests.test_utils as utils
from hooks.clang_format import ClangFormatCmd
from hooks.clang_tidy import ClangTidyCmd
from hooks.cppcheck import CppcheckCmd
from hooks.cpplint import CpplintCmd
from hooks.include_what_you_use import IncludeWhatYouUseCmd
from hooks.oclint import OCLintCmd
from hooks.uncrustify import UncrustifyCmd


class TestVersions:
    """Test the --version flag for hooks: clang-format, clang-tidy, and oclint."""

    err_ver = "0.0.0"
    versions = utils.get_versions()
    err_str = """Problem with {0}: Version of {0} is wrong
Expected version: {1}
Found version: {2}
Edit your pre-commit config or use a different version of {0}.
"""

    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests"""
        cls.scenarios = cls.generate_table_tests()

    @classmethod
    def generate_table_tests(cls):
        """Run table tests for versions for all commands."""
        scenarios = []
        commands = [
            ClangFormatCmd,
            ClangTidyCmd,
            UncrustifyCmd,
            CppcheckCmd,
            CpplintCmd,
            IncludeWhatYouUseCmd,
        ]  # noqa: E501
        if os.name != "nt":  # oclint is not supported on windows
            commands.append(OCLintCmd)
        for cmd in commands:
            actual_ver = cls.versions[cmd.command]
            err_str = cls.err_str.format(cmd.command, cls.err_ver, actual_ver).encode()
            # Removing last char ~= having actual version be $ver-beta or $ver.5
            fuzzy_version = actual_ver[:-1]

            table_tests = [
                ["base", cmd, actual_ver, b"", 0],
                ["fuzzy", cmd, fuzzy_version, b"", 0],
                ["error", cmd, cls.err_ver, err_str, 1],
            ]
            for t in table_tests:
                scenarios += [
                    [
                        "({}) {} --version {}".format(t[0], cmd.command, t[2]),
                        {"cmd_class": t[1], "version": t[2], "expected_stderr": t[3], "expected_retcode": t[4]},
                    ]
                ]
        return scenarios

    @staticmethod
    def test_version(cmd_class, version, expected_stderr, expected_retcode):
        args = [cmd_class.command + "-hook", "--version", version]
        sp_child = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        actual_stderr = sp_child.stderr
        actual_retcode = sp_child.returncode
        utils.assert_equal(actual_stderr, expected_stderr)
        assert actual_retcode == expected_retcode
