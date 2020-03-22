"""Config file for pytest
Taken from
    https://docs.pytest.org/en/latest/example/simple.html
"""
import shutil

import pytest


def pytest_addoption(parser):
    """Add --runslow parse option for tests that take > 1s."""
    action = "store_true"
    shelp = "run slow tests"
    parser.addoption("--runslow", action=action, default=False, help=shelp)
    ihelp = "run internal tests"
    parser.addoption("--internal", action=action, default=False, help=ihelp)


def pytest_collection_modifyitems(config, items):
    """Add pytest.mark.slow option to mark tests that take > 1s.
    Add pytest.mark.develop option to mark tests that check internals."""
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    skip_internal = pytest.mark.skip(reason="need --internal option to run")
    for item in items:
        if "cmd_class" in item.name and not config.getoption("--internal"):
            item.add_marker(skip_internal)
        runs_slow = "oclint" in item.name
        if runs_slow and not config.getoption("--runslow"):
            item.add_marker(skip_slow)


def pytest_exception_interact(node, call, report):
    """See https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_exception_interact"""  # noqa: E501
    if report.failed:
        # Clean up temp dirs in tests/files if a test failed.
        shutil.rmtree("tests/files/temp")
