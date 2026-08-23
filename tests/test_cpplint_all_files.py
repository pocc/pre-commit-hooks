#!/usr/bin/env python3
"""Regression test: cpplint reports errors from every file, not just the first (#64)."""
import io
import os
import tempfile
from contextlib import redirect_stderr

import pytest

from hooks.cpplint import CpplintCmd

BAD = "int main(){int i;return;}\n"  # whitespace + missing-copyright errors


@pytest.fixture
def two_bad_files():
    paths = []
    for name in ("first_bad.c", "second_bad.c"):
        d = tempfile.mkdtemp()
        p = os.path.join(d, name)
        with open(p, "w") as f:
            f.write(BAD)
        paths.append(p)
    yield paths
    for p in paths:
        if os.path.exists(p):
            os.unlink(p)


def test_reports_all_files_before_exit(two_bad_files):
    cmd = CpplintCmd(["cpplint-hook", *two_bad_files])
    buf = io.BytesIO()
    with pytest.raises(SystemExit) as exc:
        with redirect_stderr(io.TextIOWrapper(buf)):
            cmd.run()
    assert exc.value.code != 0
    output = cmd.stdout + cmd.stderr
    # Both files must appear; the old code exited after the first one.
    for p in two_bad_files:
        assert os.path.basename(p).encode() in output, f"{p} missing from output"
