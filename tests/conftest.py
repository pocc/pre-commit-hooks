"""Config file for pytest
Taken from
    https://docs.pytest.org/en/latest/example/simple.html
"""
import pytest


def pytest_addoption(parser):
    """Add --runslow parse option for tests that take > 1s."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Add pytest.mark.slow option to mark tests that take > 1s."""
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
