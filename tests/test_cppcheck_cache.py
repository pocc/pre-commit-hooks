#!/usr/bin/env python3
"""Tests for cppcheck persistent caching (#83, #84)."""
import multiprocessing
import shutil
from pathlib import Path

import pytest

from hooks.cppcheck import BUILD_DIR_OPTION
from hooks.cppcheck import CppcheckCmd
from hooks.utils import file_lock


def _hold_lock(cache_dir, attempting, entered, release):
    attempting.set()
    with file_lock(str(Path(cache_dir) / ".lock")):
        entered.set()
        release.wait(5)


def test_build_dir_is_split_by_source_path(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    files = [tmp_path / "first" / "foo.cpp", tmp_path / "second" / "foo.cpp"]
    for path in files:
        path.parent.mkdir()
        path.write_text("int main() { return 0; }\n")
    cmd = CppcheckCmd(["cppcheck-hook", f"{BUILD_DIR_OPTION}={cache_root}", "-j", "4", *(str(path) for path in files)])
    calls = []
    monkeypatch.setattr(cmd, "run_command", lambda args: calls.append(args))
    monkeypatch.setattr(cmd, "exit_on_error", lambda: None)

    cmd.run()

    build_dirs = [
        Path(next(arg.split("=", 1)[1] for arg in call if arg.startswith(BUILD_DIR_OPTION + "="))) for call in calls
    ]
    assert build_dirs[0] != build_dirs[1]
    assert all(path.parent == cache_root and path.is_dir() for path in build_dirs)
    assert all("-j" in call and "4" in call for call in calls)


def test_cached_mode_runs_one_file_list(tmp_path, monkeypatch):
    cache_root = tmp_path / "cache"
    files = [tmp_path / "first.c", tmp_path / "second.c"]
    for path in files:
        path.write_text("int main() { return 0; }\n")
    cmd = CppcheckCmd(
        [
            "cppcheck-cached-hook",
            f"{BUILD_DIR_OPTION}={cache_root}",
            "-j",
            "4",
            *(str(path) for path in files),
        ],
        cached=True,
    )
    calls = []
    monkeypatch.setattr(cmd, "run_command", lambda args, input_data=None: calls.append((args, input_data)))
    monkeypatch.setattr(cmd, "exit_on_error", lambda: None)

    cmd.run()

    assert calls == [(cmd.args + ["--file-list=-"], "\n".join(str(path) for path in files).encode())]
    assert (cache_root / ".lock").is_file()


def test_cached_mode_requires_build_dir(tmp_path, capfd):
    source = tmp_path / "source.c"
    source.write_text("int main() { return 0; }\n")
    cmd = CppcheckCmd(["cppcheck-cached-hook", str(source)], cached=True)

    with pytest.raises(SystemExit) as error:
        cmd.run()

    assert error.value.code == 1
    assert "cppcheck-cached requires --cppcheck-build-dir=<path>." in capfd.readouterr().err


@pytest.mark.skipif(shutil.which("cppcheck") is None, reason="cppcheck is not installed")
def test_cached_mode_keeps_same_basenames_distinct(tmp_path):
    cache_root = tmp_path / "cache"
    files = [tmp_path / "first" / "foo.c", tmp_path / "second" / "foo.c"]
    for path in files:
        path.parent.mkdir()
        path.write_text("int main() { return 0; }\n")

    CppcheckCmd(
        [
            "cppcheck-cached-hook",
            f"{BUILD_DIR_OPTION}={cache_root}",
            "-j",
            "4",
            *(str(path) for path in files),
        ],
        cached=True,
    ).run()

    index = (cache_root / "files.txt").read_text()
    assert all(str(path) in index for path in files)
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


@pytest.mark.skipif(shutil.which("cppcheck") is None, reason="cppcheck is not installed")
def test_same_basename_cache_does_not_reuse_another_path(tmp_path):
    cache_root = tmp_path / "cache"
    first = tmp_path / "first" / "foo.cpp"
    second = tmp_path / "second" / "foo.cpp"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("int main(){int i;return;}\n")
    second.write_text(first.read_text())
    suppression = f"--suppress=unusedVariable:{first}"

    def run(source):
        cmd = CppcheckCmd(["cppcheck-hook", f"{BUILD_DIR_OPTION}={cache_root}", suppression, str(source)])
        returncode = 0
        try:
            cmd.run()
        except SystemExit as exc:
            returncode = int(exc.code)
        return returncode, cmd.stdout + cmd.stderr

    assert run(first)[0] == 0
    cold_returncode, cold_output = run(second)
    warm_returncode, warm_output = run(second)

    assert cold_returncode == warm_returncode == 1
    assert str(second).encode() in cold_output
    assert str(second).encode() in warm_output
