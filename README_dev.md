## Repo Development

Use this document to get a lower-level understanding of this repo.
This should provide the information needed to add a new hook.

### Adding a hook

* [ ] Add the hook to hooks/
* [ ] Add tests to tests/test_hooks.py (or alternative file)
* [ ] Add tests to tests/test_versions.py
* [ ] Add a section in .pre-commit-hooks.yaml
* [ ] Add a line to setup.cfg
* [ ] Update tests/test_utils.py get_versions() regex and command list
* [ ] Update the README.md

### Standalone Hooks

You can also use these hooks on the command line for testing purposes or if you like consistent return codes.
These hooks are available via [PyPI](https://pypi.org/project/CLinters/).
Install it with `pip install CLinters`.
They are named as `$cmd-hook`, creating clang-format-hook, clang-tidy-hook, oclint-hook, cppcheck-hook, and uncrustify-hook.

They are generated with setup.py and setup.cfg and can be found in ~/.local/bin (at least on linux).
To test changes in hooks with pdb, using uncrustify-hook as an example (with uncrustify args following the command), use the following snippet:

    python3 -m pdb "$(which uncrustify-hook)" -l cpp -c uncrustify_defaults.cfg err.cpp

And add `breakpoint()` wherever you want pdb to trigger.

### Testing

*If tests fail, it may be due to a new version of a command.*
*Known good command versions/OSes are at tests/pass_configurations.md*

If you want to run these tests, you will need to install the command line versions
of the hooks locally with `pip install .`.

To run the tests and verify `clang-format`, `clang-tidy`, and `oclint` are
working as expected on your system, use `pytest --oclint --internal -vvv`.
This will work on both bash and python branches.

Testing is done by using pytest to generate 76 table tests (python branch)
based on combinations of args, files, and expected results.

The default is to skip most (41/76) tests as to run them all takes ~60s. These
pytest options are available to add test types:

* `--oclint`: oclint tests, which take extra time
* `--internal`: Internal class tests for internal consistency

**Note**: You can parallelize these tests with `pytest-xdist` (run `pip install pytest-xdist`). For example, adding `-n 4`
to the command creates 4 workers.

To run all tests serially, run `pytest -x -vvv --internal --oclint` like so:

```bash
pre-commit-hooks$ pytest -x -vvv --internal --oclint
============================= test session starts ==============================
platform darwin -- Python 3.7.6, pytest-5.4.1, py-1.7.0, pluggy-0.13.1 -- /usr/local/opt/python/bin/python3.7
cachedir: .pytest_cache
rootdir: /Users/pre-commit-hooks/code/pre-commit-hooks, inifile: pytest.ini
collected 76 items

tests/test_hooks.py::TestHooks::test_run[run_cmd_class clang-format on /Users/pre-commit-hooks/code/pre-commit-hooks/tests/files/ok.c] PASSED [  3%]
tests/test_hooks.py::TestHooks::test_run[run_cmd_class clang-tidy on /Users/pre-commit-hooks/code/pre-commit-hooks/tests/files/ok.c] PASSED [  7%]
...

============================= 93 passed in 9.28s ==============================
```

### Why have a script when your hook could be `$command "$@"`?

shellcheck keeps things simple by relaying arguments as `shellcheck "$@"`.
This is not possible with several C/C++ linters because they exit 0 when
there are errors. The pre-commit framework registers failures by non-zero exit codes,
which results in false "passes". Additionally, these scripts provide more verbose error
messages and version locking.
