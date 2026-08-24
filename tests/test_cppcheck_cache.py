#!/usr/bin/env python3
"""Tests for cppcheck persistent caching."""
import hashlib
import multiprocessing
import os
import shutil
import sys
from pathlib import Path

import pytest

from hooks.cppcheck import BUILD_DIR_OPTION
from hooks.cppcheck import CppcheckCmd
from hooks.cppcheck import NO_CACHE_OPTION
from hooks.utils import file_lock


def _hold_lock(cache_dir, attempting, entered, release):
    attempting.set()
    with file_lock(str(Path(cache_dir) / ".lock")):
        entered.set()
        release.wait(5)


def test_default_cache_runs_one_file_list(tmp_path, monkeypatch):
    files = [tmp_path / "first" / "foo.cpp", tmp_path / "second" / "foo.cpp"]
    for path in files:
        path.parent.mkdir()
        path.write_text("int main() { return 0; }\n")
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.chdir(repo)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / "cache"))
    monkeypatch.setenv("LOCALAPPDATA", str(home / "local"))
    cmd = CppcheckCmd(["cppcheck-hook", *(str(path) for path in files)])
    calls = []
    monkeypatch.setattr(cmd, "get_version_str", lambda: "2.19.0")
    monkeypatch.setattr(
        cmd, "run_command", lambda args, input_data=None: calls.append((args, input_data))
    )
    monkeypatch.setattr(cmd, "exit_on_error", lambda: None)

    cmd.run()

    if os.name == "nt":
        cache_home = home / "local"
    elif sys.platform == "darwin":
        cache_home = home / "Library" / "Caches"
    else:
        cache_home = home / "cache"
    cache_root = cache_home / "pre-commit-hooks" / "cppcheck" / "2.19.0"
    cache_root /= hashlib.sha256(
        os.path.normcase(os.path.abspath(repo)).encode()
    ).hexdigest()
    assert calls == [
        (cmd.args + ["--file-list=-"], "\n".join(str(path) for path in files).encode())
    ]
    assert f"{BUILD_DIR_OPTION}={cache_root}" in cmd.args
    assert "-j" in cmd.args and str(os.cpu_count() or 1) in cmd.args
    assert (cache_root / ".lock").is_file()


def test_explicit_cache_and_jobs_override_defaults(tmp_path, monkeypatch):
    source = tmp_path / "source.c"
    source.write_text("int main() { return 0; }\n")
    cache_root = tmp_path / "cache"
    cmd = CppcheckCmd(
        ["cppcheck-hook", f"{BUILD_DIR_OPTION}={cache_root}", "-j", "4", str(source)]
    )
    calls = []
    monkeypatch.setattr(
        cmd,
        "get_version_str",
        lambda: pytest.fail("explicit cache must not query the version"),
    )
    monkeypatch.setattr(
        cmd, "run_command", lambda args, input_data=None: calls.append((args, input_data))
    )
    monkeypatch.setattr(cmd, "exit_on_error", lambda: None)

    cmd.run()

    assert calls == [(cmd.args + ["--file-list=-"], str(source).encode())]
    assert "-j" in cmd.args and "4" in cmd.args
    assert (cache_root / ".lock").is_file()


def test_no_cache_omits_build_directory(tmp_path, monkeypatch):
    source = tmp_path / "source.c"
    source.write_text("int main() { return 0; }\n")
    cmd = CppcheckCmd(["cppcheck-hook", NO_CACHE_OPTION, str(source)])
    calls = []
    monkeypatch.setattr(
        cmd,
        "get_version_str",
        lambda: pytest.fail("disabled cache must not query the version"),
    )
    monkeypatch.setattr(
        cmd, "run_command", lambda args, input_data=None: calls.append((args, input_data))
    )
    monkeypatch.setattr(cmd, "exit_on_error", lambda: None)

    cmd.run()

    assert calls == [(cmd.args + ["--file-list=-"], str(source).encode())]
    assert NO_CACHE_OPTION not in cmd.args
    assert not any(arg.startswith(BUILD_DIR_OPTION) for arg in cmd.args)


@pytest.mark.skipif(shutil.which("cppcheck") is None, reason="cppcheck is not installed")
def test_cached_run_keeps_same_basenames_distinct(tmp_path):
    cache_root = tmp_path / "cache"
    files = [tmp_path / "first" / "foo.c", tmp_path / "second" / "foo.c"]
    for path in files:
        path.parent.mkdir()
        path.write_text("int main() { return 0; }\n")

    CppcheckCmd(
        [
            "cppcheck-hook",
            f"{BUILD_DIR_OPTION}={cache_root}",
            "-j",
            "4",
            *(str(path) for path in files),
        ],
    ).run()

    index = (cache_root / "files.txt").read_text().replace("\\", "/")
    assert all(str(path).replace("\\", "/") in index for path in files)
    assert len(list(cache_root.glob("foo.a*"))) == 2


def test_cache_lock_serializes_processes(tmp_path):
    context = multiprocessing.get_context("spawn")
    first_attempting = context.Event()
    second_attempting = context.Event()
    first_entered = context.Event()
    second_entered = context.Event()
    release = context.Event()
    first = context.Process(target=_hold_lock, args=(str(tmp_path), first_attempting, first_entered, release))
    second = context.Process(target=_hold_lock, args=(str(tmp_path), second_attempting, second_entered, release))

    try:
        first.start()
        assert first_entered.wait(5)
        second.start()
        assert second_attempting.wait(5)
        assert not second_entered.wait(0.2)
        release.set()
        assert second_entered.wait(5)
    finally:
        release.set()
        for process in (first, second):
            process.join(5)
            if process.is_alive():
                process.terminate()
                process.join(5)

    assert first.exitcode == second.exitcode == 0
