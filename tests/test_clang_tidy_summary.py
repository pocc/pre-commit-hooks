#!/usr/bin/env python3
"""Warnings clang-tidy suppresses in headers must not fail the hook (#85)."""
import shutil

import pytest

from hooks.clang_tidy import ClangTidyCmd

pytestmark = pytest.mark.skipif(shutil.which("clang-tidy") is None, reason="clang-tidy not installed")

# Both helper() and own() trigger readability-else-after-return.
HEADER = """\
#pragma once

static int helper(int x) {
  if (x) {
    return 1;
  } else {
    return 2;
  }
}
"""

MAIN_WITHOUT_WARNINGS = """\
#include "h.h"

int main(void) { return helper(0); }
"""

MAIN_WITH_WARNING = """\
#include "h.h"

int own(int x) {
  if (x) {
    return 1;
  } else {
    return 2;
  }
}

int main(void) { return helper(0) + own(0); }
"""


def run_clang_tidy_hook(tmp_path, main_source, compiler_args=()):
    """Write h.h and main.c, run the hook on main.c, and return its exit code."""
    (tmp_path / "h.h").write_text(HEADER)
    main = tmp_path / "main.c"
    main.write_text(main_source)
    args = [
        "clang-tidy-hook",
        "-checks=-*,readability-else-after-return,clang-diagnostic-deprecated",
        "--header-filter=^$",  # h.h is not user code, so clang-tidy suppresses its warning
        str(main),
        "--",
        *compiler_args,
    ]
    try:
        ClangTidyCmd(args).run()
    except SystemExit as e:
        return e.code
    return 0


def test_warning_only_in_header_passes(tmp_path):
    assert run_clang_tidy_hook(tmp_path, MAIN_WITHOUT_WARNINGS) == 0


def test_warning_about_build_command_passes(tmp_path):
    # Compiling a .c file as C++ prints "warning: treating 'c' input as 'c++' ..." with no
    # file location. CMake projects on Windows hit this (see tests/test_iss36.py).
    assert run_clang_tidy_hook(tmp_path, MAIN_WITHOUT_WARNINGS, ["--driver-mode=g++"]) == 0


def test_warning_in_checked_file_fails(tmp_path):
    assert run_clang_tidy_hook(tmp_path, MAIN_WITH_WARNING) == 1
