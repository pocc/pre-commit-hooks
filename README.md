# pre-commit hooks

This is a [pre-commit](https://pre-commit.com) hooks repo that
integrates C/C++ linters [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html), [clang-tidy](https://clang.llvm.org/extra/clang-tidy/), and [oclint](http://oclint.org/).

## Example Usage

With `int main() { int i; return 10; }` in a file, all three linters should fail on commit:

<img src="https://dl.dropboxusercontent.com/s/xluan7x39wx6fss/c_linters_failing.png" width="66%" height="66%">

Using clang-format `8.0.0`; clang-tidy `8.0.0`; oclint `0.13`

The above uses this `.pre-commit-config.yaml`:

```yaml
fail_fast: false
repos:
  - repo: https://github.com/pocc/pre-commit-hooks
    rev: python
    hooks:
      - id: clang-format
        args: [--style=Google, -i]
      - id: clang-tidy
        args: [-checks=*, -warnings-as-errors=*]
      - id: oclint
        args: [-enable-clang-static-analyzer, -enable-global-analysis]
      - id: uncrustify
      - id: cppcheck
        args: [-enable=all]
```

_Note that for your config yaml, you can supply your own args or remove the args line entirely,
depending on your use case._

## Using the Hooks

### Prerequisites

_You will need to install these utilities in order to use them._ _Your package
manager may already have them._

- `brew install llvm oclint`
- `apt install clang-format clang-tidy`

Bash is required to use these hooks as all 3 invoking scripts are written in it.

### Hook Info

|                                                                          | Type                 | Languages                             | Fix Inplace               | Enable all checks                                     |
| ------------------------------------------------------------------------ | -------------------- | ------------------------------------- | ------------------------- | ----------------------------------------------------- |
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | Formatter            | C, C++, ObjC                          | -i                        |                                                       |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | Stacic code analyzer | C, C++, ObjC                          | --fix-errors [1]          | -checks=*, -warnings-as-errors=*                      |
| [oclint](http://oclint.org/)                                             | Static code analyzer | C, C++, ObjC                          |                           | -enable-global-analysis -enable-clang-static-analyzer |
| [uncrustify](http://uncrustify.sourceforge.net/)                         | Formatter            | C, C++, C#, ObjC, D, Java, Pawn, VALA | --replace --no-backup [2] |                                                       |
| [cppcheck](http://cppcheck.sourceforge.net/)                             | Static code analyzer | C, C++                                |                           | -enable=all                                           |

[1]: `-fix` will fail if there are compiler errors. `-fix-errors` will `-fix`
and fix compiler errors if it can, like missing semicolons.

[2]: By definition, if you are using `pre-commit`, you are using version control.
Therefore, it is recommended to avoid needless backup creation by using `--no-backup`.

### Enforcing linter version with --version

Some linters change behavior between versions. To enforce a linter version
8.0.0, for example, add `--version=8.0.0` to `args:` for that linter. Note that
this is a pre-commit hook arg and passing it to the linter will cause an error.

### Compilation Database

`clang-tidy` and `oclint` both expect a
[compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html).
Both of the hooks for them will ignore the error for not having one.

You can generate with one `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ...` if you
have a cmake-based project.

### The -- option

Options after `--` like `-std=c++11` will be interpreted correctly for
`clang-tidy` and `oclint`. Make sure they sequentially follow the `--` argument
in the hook's args list.

## Testing

To run the tests and verify `clang-format`, `clang-tidy`, and `oclint` are
working as expected on your system, use `pytest --runslow --internal -vvv`.
This will work on both bash and python branches.

Testing is done by using pytest to generate 76 table tests (python branch)
based on combinations of args, files, and expected results.

The default is to skip most (41/76) tests as to run them all takes ~60s. These
pytest options are available to add test types:

* `--runslow`: oclint tests, which take extra time
* `--internal`: Internal class tests to ensure internal/shell APIs match

**Note**: You can parallelize these tests with `pytest-xdist`. Adding `-n 32`
to the command creates 32 workers and divides runtime by ~6x in my testing.

To run all tests serially, run `pytest -x -vvv --internal --runslow` like so:

```bash
pre-commit-hooks$ pytest -x -vvv --internal --runslow
============================= test session starts ==============================
platform darwin -- Python 3.7.6, pytest-5.4.1, py-1.7.0, pluggy-0.13.1 -- /usr/local/opt/python/bin/python3.7
cachedir: .pytest_cache
rootdir: /Users/pre-commit-hooks/code/pre-commit-hooks, inifile: pytest.ini
collected 76 items

tests/test_hooks.py::TestHooks::test_run[run_cmd_class clang-format on /Users/pre-commit-hooks/code/pre-commit-hooks/tests/files/ok.c] PASSED [  3%]
tests/test_hooks.py::TestHooks::test_run[run_cmd_class clang-tidy on /Users/pre-commit-hooks/code/pre-commit-hooks/tests/files/ok.c] PASSED [  7%]
...

============================= 76 passed in 61.86s ==============================
```

## Additional Resources

### clang-format

* [Official Docs](https://clang.llvm.org/docs/ClangFormatStyleOptions.html)
* [clang-format
  Guide](https://embeddedartistry.com/blog/2017/10/23/creating-and-enforcing-a-coding-standard-with-clang-format) -
  a good overview and a great place to get started
* [clang-format Configurator](https://zed0.co.uk/clang-format-configurator/) - Website to
  interactively design your config while
* [clang-format Options Explorer](https://clangformat.com/) - Website to interactively
  understand various options
* [Source Code](https://github.com/llvm-mirror/clang/tree/master/tools/clang-format)

### clang-tidy

* [Official Docs](https://clang.llvm.org/extra/clang-tidy/)
* [clang-tidy
  guide](https://www.kdab.com/clang-tidy-part-1-modernize-source-code-using-c11c14/) -
  Good place to start
* [Example
  usage](https://github.com/KratosMultiphysics/Kratos/wiki/How-to-use-Clang-Tidy-to-automatically-correct-code) -
  Explanation of how to use clang-tidy by the creators of Kratos
* [Add your own
  checks](https://devblogs.microsoft.com/cppblog/exploring-clang-tooling-part-1-extending-clang-tidy/) -
  Function names must be _awesome_!
* [Source Code](https://github.com/llvm-mirror/clang-tools-extra/tree/master/clang-tidy)

### oclint

* [Official Docs](http://oclint.org/)
* [Fastlane Integration](https://docs.fastlane.tools/actions/oclint/)
* [Source Code](https://github.com/oclint/oclint)

### uncrustify

* [Official Docs](http://uncrustify.sourceforge.net/)
* [Getting Started with Uncrustify](https://patrickhenson.com/2018/06/07/uncrustify-configuration.html)
* [Source Code](https://github.com/uncrustify/uncrustify)

### cppcheck

* [Official Docs](http://cppcheck.sourceforge.net/)
* [Using Cppcheck](https://katecpp.wordpress.com/2015/08/04/cppcheck/)
* [Source Code](https://github.com/danmar/cppcheck)

## License

Apache 2.0
