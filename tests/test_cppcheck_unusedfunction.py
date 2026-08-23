#!/usr/bin/env python3
"""unusedFunction is suppressed for per-file runs but left enabled under --project."""
import os
import tempfile

import pytest

from hooks.cppcheck import CppcheckCmd


@pytest.fixture
def c_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        f.write("int main() { return 0; }\n")
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_unusedfunction_suppressed_per_file(c_file):
    cmd = CppcheckCmd(["cppcheck-hook", c_file])
    assert "--suppress=unusedFunction" in cmd.args


def test_unusedfunction_kept_with_project(c_file):
    # Whole-program mode: the check is valid, so it must not be force-suppressed.
    cmd = CppcheckCmd(["cppcheck-hook", "--project=compile_commands.json", c_file])
    assert "--suppress=unusedFunction" not in cmd.args
    # The other defaults still apply.
    assert "--suppress=unmatchedSuppression" in cmd.args
    assert "--suppress=missingIncludeSystem" in cmd.args
