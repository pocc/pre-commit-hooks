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
    temp_dir = os.path.join("tests/files/temp", uuid_dir)
    os.makedirs(temp_dir)
    new_temp_name = shutil.copy2(filename, temp_dir)
    return os.path.join(os.getcwd(), new_temp_name)


def assert_equal(expected, actual):
    """Stand in for Python's assert which is annoying to work with."""
    if expected != actual:
        print(b"Expected:`" + expected + b"`")
        print(b"Actual:`" + actual + b"`")
        diff_lines = difflib.diff_bytes(difflib.unified_diff, expected, actual)
        print(b"\n".join(diff_lines))
        pytest.fail("Test failed!")


def get_versions():
    """Returns a dict of commands and their versions."""
    commands = ["clang-format", "clang-tidy", "uncrustify", "cppcheck"]
    if os.name != "nt":  # oclint doesn't work on windows
        commands += ["oclint"]
    # Regex for all versions. Unit tests: https://regex101.com/r/ciqAuO/6/tests
    regex = r"[- ]((?:\d+\.)+\d+[_+\-a-z\d]*)(?![\s\S]*[- ]\d\.)"
    versions = {}
    for cmd in commands:
        if not shutil.which(cmd):
            sys.exit("Command " + cmd + " not found.")
        cmds = [cmd, "--version"]
        child = sp.run(cmds, stdout=sp.PIPE, stderr=sp.PIPE)
        output = child.stdout.decode("utf-8")
        try:
            versions[cmd] = re.search(regex, output).group(1)
        except AttributeError:
            print("Received `" + output + "`. Version regexes have broken.")
            print("Please file a bug (github.com/pocc/pre-commit-hooks).")
            sys.exit(1)
    return versions
