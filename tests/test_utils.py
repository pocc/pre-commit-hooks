#!/usr/bin/env python3
import difflib
import os
import re
import shutil
import subprocess as sp
import sys
import uuid

import pytest


def create_temp_dir_for(filename):
    """Create a temporary dir for a file, returning the file path."""
    uuid_dir = str(uuid.uuid4())
    temp_dir = os.path.join("tests/test_repo/temp", uuid_dir)
    os.makedirs(temp_dir)
    new_temp_name = shutil.copy2(filename, temp_dir)
    return os.path.join(os.getcwd(), new_temp_name)


def assert_equal(expected, actual):
    """Stand in for Python's assert which is annoying to work with."""
    if expected != actual:
        print(f"\n\nExpected:`{expected}`")
        print(f"\n\nActual:`{actual}`")
        if isinstance(expected, bytes) and isinstance(actual, bytes):
            expected_str = expected.decode()
            actual_str = actual.decode()
            print("String comparison:", expected_str == actual_str)
            diff_lines_gen = difflib.context_diff(expected_str, actual_str, "Expected", "Actual")
            diff_lines = "".join(list(diff_lines_gen))
            print(f"\n\nDifference:\n{diff_lines}")
        else:
            print(f"Expected is type {type(expected)}\nActual is type {type(actual)}")
        pytest.fail("Test failed!")


def get_versions():
    """Returns a dict of commands and their versions."""
    commands = ["clang-format", "clang-tidy", "uncrustify", "cppcheck", "cpplint", "include-what-you-use"]
    if os.name != "nt":  # oclint doesn't work on windows
        commands += ["oclint"]
    # Regex for all versions. Unit tests: https://regex101.com/r/w5P74Q/1
    regex = r"[- ]((?:\d+\.)+\d+[_+\-a-z\d]*)(?![\s\S]*OCLint version)"
    versions = {}
    for cmd in commands:
        if not shutil.which(cmd):
            sys.exit("Command " + cmd + " not found.")
        cmds = [cmd, "--version"]
        child = sp.run(cmds, stdout=sp.PIPE, stderr=sp.PIPE)
        if len(child.stderr) > 0:
            print(f"Received error when running {cmds}:\n{child.stderr}")
            sys.exit(1)
        output = child.stdout.decode("utf-8")
        try:
            versions[cmd] = re.search(regex, output).group(1)
        except AttributeError:
            print(f"Received `{output}`. Version regexes have broken.")
            print("Please file a bug (github.com/pocc/pre-commit-hooks).")
            sys.exit(1)
    return versions


# Required for testing with clang-tidy and oclint
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
