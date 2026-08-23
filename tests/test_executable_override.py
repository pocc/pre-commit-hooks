#!/usr/bin/env python3
"""A command's executable can be overridden by an env var named after it (#57)."""
import os
import tempfile

import pytest

from hooks.cppcheck import CppcheckCmd
from hooks.clang_tidy import ClangTidyCmd


@pytest.fixture
def c_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        f.write("int main() { return 0; }\n")
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


def test_default_executable_is_command_name(c_file):
    cmd = CppcheckCmd(["cppcheck-hook", c_file])
    assert cmd.executable == "cppcheck"
    assert cmd.command == "cppcheck"


def test_env_var_overrides_executable(c_file, monkeypatch):
    monkeypatch.setenv("CPPCHECK", "/opt/custom/bin/cppcheck")
    cmd = CppcheckCmd(["cppcheck-hook", c_file])
    assert cmd.executable == "/opt/custom/bin/cppcheck"
    # identity is preserved for messages and analyzer detection
    assert cmd.command == "cppcheck"


def test_hyphenated_command_env_var(c_file, monkeypatch):
    monkeypatch.setenv("CLANG_TIDY", "/opt/llvm/bin/clang-tidy")
    cmd = ClangTidyCmd(["clang-tidy-hook", c_file])
    assert cmd.executable == "/opt/llvm/bin/clang-tidy"
    assert cmd.command == "clang-tidy"


def test_multiword_command_env_var(c_file, monkeypatch):
    # include-what-you-use -> INCLUDE_WHAT_YOU_USE. executable resolves from
    # self.command, so exercise the multi-word derivation without a hook that
    # runs check_installed in its constructor.
    monkeypatch.setenv("INCLUDE_WHAT_YOU_USE", "/usr/local/bin/iwyu")
    cmd = CppcheckCmd(["cppcheck-hook", c_file])
    cmd.command = "include-what-you-use"
    assert cmd.executable == "/usr/local/bin/iwyu"


def test_unset_env_does_not_override(c_file, monkeypatch):
    monkeypatch.delenv("CPPCHECK", raising=False)
    cmd = CppcheckCmd(["cppcheck-hook", c_file])
    assert cmd.executable == "cppcheck"
