#!/usr/bin/env python3
"""Vala support via the uncrustify-vala hook (#87)."""
import os
import re
import shutil

import pytest
import yaml
from identify import identify

from hooks.uncrustify import UncrustifyCmd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNC_DEFAULTS = os.path.join(REPO_ROOT, "tests", "uncrustify_defaults.cfg")

UNFORMATTED = b'public class Hello : Object {\npublic static int main (string[] args) {\nstdout.printf ("hi");\nreturn 0;\n}\n}\n'


def load_hook(hook_id):
    with open(os.path.join(REPO_ROOT, ".pre-commit-hooks.yaml")) as f:
        hooks = yaml.safe_load(f)
    return next(h for h in hooks if h["id"] == hook_id)


def test_manifest_matches_vala_by_extension():
    hook = load_hook("uncrustify-vala")
    assert hook["entry"] == "uncrustify-hook"
    # Must not depend on identify knowing a `vala` tag (only in identify>=2.6.21).
    assert "vala" not in hook.get("types", []) + hook.get("types_or", [])
    assert set(hook["types"]) <= identify.ALL_TAGS
    files_re = re.compile(hook["files"])
    for name in ["main.vala", "src/ui/Window.vala", "LEGACY.VALA"]:
        assert files_re.search(name), name
    for name in ["main.c", "vala.txt", "main.vala.bak", "main.vapi"]:
        assert not files_re.search(name), name


@pytest.mark.skipif(shutil.which("uncrustify") is None, reason="uncrustify not installed")
def test_uncrustify_formats_vala(tmp_path, capfdbinary):
    src = tmp_path / "hello.vala"
    src.write_bytes(UNFORMATTED)
    cmd = UncrustifyCmd(["uncrustify-hook", "-c", UNC_DEFAULTS, str(src)])
    with pytest.raises(SystemExit) as exc:
        cmd.run()
    assert exc.value.code == 1
    assert b"+  public static int main(string[] args) {" in capfdbinary.readouterr().out

    # Writing uncrustify's output back byte-for-byte makes the hook pass.
    src.write_bytes(b"\n".join(cmd.get_formatted_lines(str(src))))
    UncrustifyCmd(["uncrustify-hook", "-c", UNC_DEFAULTS, str(src)]).run()
