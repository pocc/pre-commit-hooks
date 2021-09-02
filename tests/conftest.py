"""Config file for pytest
Taken from
    https://docs.pytest.org/en/latest/example/simple.html
"""
import os
import shutil

import pytest


def pytest_addoption(parser):
    """Add --internal option for testing classes (this is mostly redundant)"""
    action = "store_true"
    ihelp = "run internal tests"
    parser.addoption("--internal", action=action, default=False, help=ihelp)


def pytest_collection_modifyitems(config, items):
    """Add pytest.mark.internal option to mark tests that check internals."""
    skip_internal = pytest.mark.skip(reason="need --internal option to run")
    for item in items:
        if "cmd_class" in item.name and not config.getoption("--internal"):
            item.add_marker(skip_internal)


def pytest_exception_interact(node, call, report):
    """See https://docs.pytest.org/en/latest/reference.html#_pytest.hookspec.pytest_exception_interact"""  # noqa: E501
    if report.failed:
        # Clean up temp dirs in tests/test_repo if a test failed.
        if os.path.exists("tests/test_repo/temp"):
            shutil.rmtree("tests/test_repo/temp")
        # Delete generated files
        for filename in ["ok.plist", "err.plist", "defaults.cfg"]:
            abs_filename = os.path.abspath(filename)
            if os.path.exists(abs_filename):
                os.remove(abs_filename)


def pytest_generate_tests(metafunc):
    """Taken from pytest documentation to allow for table tests:
    https://docs.pytest.org/en/latest/example/parametrize.html#paramexamples"""
    metafunc.cls.setup_class()
    idlist = []
    argvalues = []
    argnames = []
    for scenario in metafunc.cls.scenarios:
        idlist.append(scenario[0])
        items = scenario[1].items()
        argnames = [x[0] for x in items]
        argvalues.append([x[1] for x in items])
    metafunc.parametrize(argnames, argvalues, ids=idlist, scope="class")
