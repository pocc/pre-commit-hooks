#!/usr/bin/env python3
"""Regression test for #70: --project must not be run alongside source files."""
import json
import os
import tempfile

import pytest

from hooks.cppcheck import CppcheckCmd


@pytest.fixture
def project_tree():
    d = tempfile.mkdtemp()
    src = os.path.join(d, "a.c")
    with open(src, "w") as f:
        f.write("int main(){return 0;}\n")
    cdb = os.path.join(d, "compile_commands.json")
    with open(cdb, "w") as f:
        json.dump([{"directory": d, "command": "cc -c a.c", "file": src}], f)
    cwd = os.getcwd()
    os.chdir(d)
    yield d, src, cdb
    os.chdir(cwd)


def test_project_run_omits_source_files(project_tree, capfd):
    """With --project, cppcheck is invoked without the committed file, so it does
    not fail with '--project cannot be used in conjunction with source files'."""
    d, src, cdb = project_tree
    cmd = CppcheckCmd(["cppcheck-hook", "--project=compile_commands.json", src])
    try:
        cmd.run()
    except SystemExit:
        pass
    combined = capfd.readouterr()
    assert b"--project cannot be used" not in (cmd.stdout + cmd.stderr)
    assert "--project cannot be used" not in (combined.out + combined.err)
    # the file is not passed as a positional source argument
    assert src not in cmd.args
