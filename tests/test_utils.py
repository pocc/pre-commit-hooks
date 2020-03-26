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
        print("Expected:`" + str(expected) + "`")
        print("Actual:`" + str(actual) + "`")
        diff_lines = difflib.ndiff(expected.split("\n"), actual.split("\n"))
        print("\n".join(diff_lines))
        pytest.fail("Test failed!")


def get_versions():
    """Returns a dict of commands and their versions."""
    commands = [
        "clang-format",
        "clang-tidy",
        "oclint",
        "uncrustify",
        "cppcheck",
    ]
    # Regex for all versions. Unit tests: https://regex101.com/r/ciqAuO/5/tests
    regex = r"[- ]((?:\d+\.)+\d+[_+\-a-z]*)(?![\s\S]*[- ]\d\.)"
    versions = {}
    for cmd in commands:
        output = sp.check_output([cmd, "--version"]).decode("utf-8")
        # Choose last one for sake of oclint, which outputs clang version as well
        try:
            versions[cmd] = re.search(regex, output).group(1)
        except AttributeError:
            print("Version regexes have broken.")
            print("Please file a bug (github.com/pocc/pre-commit-hooks).")
            sys.exit(1)
    return versions
