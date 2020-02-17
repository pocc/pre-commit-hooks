import pytest
import os

from hooks.clang_format_hook import main
from hooks.clang_format_hook import CMT_FAILED, CMD_MODIFIED, CMD_FAILED
from testing.utils import get_resource_path


@pytest.mark.parametrize(
    ("filename", "expected_retval"),
    (("test_free_style.cpp", CMT_FAILED), ("test_google_style.cpp", 0),),
)
def test_main(filename, expected_retval):
    ret = main([get_resource_path(filename)])
    assert ret == expected_retval


@pytest.mark.parametrize(
    ("filename", "expected_retval"),
    (("test_free_style.cpp", CMT_FAILED), ("test_google_style.cpp", 0),),
)
def test_main_verbose(filename, expected_retval):
    ret = main(["--verbose", get_resource_path(filename)])
    assert ret == expected_retval

    ret = main(["--verbose", "--style=google", get_resource_path(filename)])
    assert ret == expected_retval


@pytest.mark.parametrize(
    "filename, expected_retval",
    [("test_free_style.cpp", CMD_MODIFIED), ("test_google_style.cpp", 0),],
)
def test_inline(tmpdir, filename, expected_retval):
    f = tmpdir.join(filename)
    with open(get_resource_path(filename)) as origin:
        f.write(origin.read())
    assert main(["-i", f.strpath]) == expected_retval


@pytest.mark.parametrize(
    "filename, expected_retval",
    [("test_free_style.cpp", CMD_MODIFIED), ("test_google_style.cpp", 0),],
)
def test_inline_verbose(tmpdir, filename, expected_retval):
    f = tmpdir.join(filename)
    with open(get_resource_path(filename)) as origin:
        f.write(origin.read())
    assert main(["-i", "--verbose", f.strpath]) == expected_retval


@pytest.mark.parametrize(
    "filename, expected_retval",
    [("test_free_style.cpp", CMD_FAILED), ("test_google_style.cpp", CMD_FAILED),],
)
def test_invalid_options(tmpdir, filename, expected_retval):
    f = tmpdir.join(filename)
    with open(get_resource_path(filename)) as origin:
        f.write(origin.read())
    assert main(["-i", "--not-an-option", f.strpath]) == expected_retval
    assert main(["--not-an-option", f.strpath]) == expected_retval


@pytest.mark.parametrize(
    "filename, expected_retval",
    [("test_free_style", CMD_FAILED), ("some/test_google_style", CMD_FAILED),],
)
def test_invalid_file(tmpdir, filename, expected_retval):
    invalid_path = os.path.join(tmpdir.strpath, filename)
    assert main(["--style=google", invalid_path]) == expected_retval
    assert main(["--verbose", invalid_path]) == expected_retval
