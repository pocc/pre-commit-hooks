"""Config file for pytest
Taken from
    https://docs.pytest.org/en/latest/example/simple.html
"""
import os
import shutil

import pytest


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
    # Only apply table test generation if class has setup_class and scenarios
    if not hasattr(metafunc.cls, "setup_class") or not hasattr(
        metafunc.cls, "scenarios"
    ):
        return

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
