# pre-commit hooks

This is a [pre-commit](https://pre-commit.com) hooks repo that
integrates C/C++ linters [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html), [clang-tidy](https://clang.llvm.org/extra/clang-tidy/), and [oclint](http://oclint.org/).

## Example Usage

With `int main() { int i; return 10; }` in a file, all three linters should fail on commit:

<img src="https://dl.dropboxusercontent.com/s/xluan7x39wx6fss/c_linters_failing.png" width="66%" height="66%">

The above uses this `.pre-commit-config.yaml`:

```yaml
fail_fast: false
repos:
  - repo: https://github.com/pocc/pre-commit-hooks
    sha: master
    hooks:
      - id: clang-format
        args: [--style=Google]
      - id: clang-tidy
        args: [-checks=*, -warnings-as-errors=*]
      - id: oclint
        args: [-enable-clang-static-analyzer, -enable-global-analysis]
```

_Note that for your config yaml, you can supply your own args or remove the args line entirely,
depending on your use case._

## Using the Hooks

### Prerequisites

_You will need to install these utilities in order to use them._ _Your package
manager may already have them._

- `brew install llvm oclint`
- `apt install clang-format clang-tidy oclint`

Bash is required to use these hooks as all 3 invoking scripts are written in it.

### Hook Info

|                                                                          | What it does                                              | Fix Inplace            |
| ------------------------------------------------------------------------ | --------------------------------------------------------- | ---------------------- |
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | Formats C/C++ code according to a style                   | -i                     |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | clang-based C/C++ linter                                  | -fix, --fix-errors [1] |
| [oclint](http://oclint.org/)                                             | static code analysis tool for C, C++ and Objective-C code | N/A                    |

[1]: `-fix` will fail if there are compiler errors. `-fix-errors` will `-fix`
and fix compiler errors if it can, like missing semicolons.

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
working as expected on your system, use `pytest --runslow`. This will work
on both bash and python branches.

### Example testing with python branch

The default is to skip most (29/51) tests as to run them all takes ~60s. These
pytest options are available to add test types:

* `--runslow`: oclint and clang-tidy `-fix`/`--fix-errors` tests take extra time
* `--internal`: Internal class tests to ensure internal/shell APIs match


**Note**: You can parallelize these tests with `pytest-xdist`.
Adding `-n 16` to the command divides runtime by ~6x in my testing.

To run all tests serially, run `pytest -x -vvv --internal --runslow` like so:

```bash
pre-commit-hooks$ pytest -x -vvv --internal --runslow
============================= test session starts ==============================
platform darwin -- Python 3.7.6, pytest-5.4.1, py-1.7.0, pluggy-0.13.1 -- /usr/local/opt/python/bin/python3.7
cachedir: .pytest_cache
rootdir: /Users/pre-commit-hooks/code/pre-commit-hooks, inifile: pytest.ini
collected 27 items

tests/test_hooks.py::TestHooks::test_run[run_cmd_class clang-format on /Users/pre-commit-hooks/code/pre-commit-hooks/tests/files/ok.c] PASSED [  3%]
tests/test_hooks.py::TestHooks::test_run[run_cmd_class clang-tidy on /Users/pre-commit-hooks/code/pre-commit-hooks/tests/files/ok.c] PASSED [  7%]
...

============================= 51 passed in 61.86s ==============================
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

### oclint

* [Official Docs](http://oclint.org/)
* [Fastlane Integration](https://docs.fastlane.tools/actions/oclint/)

## License

Apache 2.0
