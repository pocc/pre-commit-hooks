#!/usr/bin/env python3
"""Integration test using a .pre-commit-config.yaml installing this repo remotely
locally in tests/test_repo"""
import os
import re
import shutil
import subprocess as sp

from tests.test_utils import assert_equal
from tests.test_utils import set_compilation_db


class TestIntegration:
    """Integration test using a sample repo."""

    @classmethod
    def setup_class(cls):
        """Create test files that will be used by other tests"""
        cls.scenarios = cls.generate_table_tests()
        files = ["ok.c", "ok.cpp", "err.c", "err.cpp"]
        filepaths = [os.path.join(os.getcwd(), f) for f in files]
        set_compilation_db(filepaths)

    @staticmethod
    def generate_table_tests():
        pre_commit_config = """\
fail_fast: false
repos:
  - repo: https://github.com/pocc/pre-commit-hooks
    rev: v1.3.3
    hooks:
      - id: clang-format
        args: [--style=Google]
      - id: clang-tidy
      - id: oclint
      - id: uncrustify
      - id: cppcheck
      - id: cpplint
      - id: include-what-you-use
"""
        expected_filename = os.path.join(os.getcwd(), "tests/test_repo/test_integration_expected_stderr.output")
        with open(expected_filename, "rb") as f:
            stderr_expected = f.read()
        stderr_expected = stderr_expected.replace(b"{repo_dir}", os.getcwd().encode())
        scenarios = [
            [
                "Integration test in tests/test_repo with a basic .pre-commit-config.yaml",
                {"pre_commit_config": pre_commit_config, "expd_output": stderr_expected},
            ]
        ]
        return scenarios

    def test_integration(self, pre_commit_config, expd_output):
        test_dir = os.path.join(os.getcwd(), "tests/test_repo")
        pre_commit_config_path = os.path.join(test_dir, ".pre-commit-config.yaml")
        with open(pre_commit_config_path, "w") as f:
            f.write(pre_commit_config)
        command_str = f"cd {test_dir}; rm -rf .git; git init; pre-commit install; git add .; git commit"
        sp_child = sp.run(["/bin/bash", "-c", command_str], stdout=sp.PIPE, stderr=sp.PIPE)
        stderr_actual = sp_child.stderr
        # Get rid of initializing messages that could interfere with test
        stderr_actual = re.sub(rb"\[INFO\].*", b"", stderr_actual)
        assert_equal(expd_output, stderr_actual)
        # Cleanup
        shutil.rmtree(os.path.join(test_dir, ".git"))


if __name__ == "__main__":
    test = TestIntegration()
    scenarios = test.generate_table_tests()
    for scenario in scenarios:
        test.test_integration(scenario[1]["pre_commit_config"], scenario[1]["expd_output"])
