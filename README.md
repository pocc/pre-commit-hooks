# pre-commit hooks

Designed to be a part of https://pre-commit.com/hooks.html. Inspired by shell
scripts in https://github.com/jumanjihouse/pre-commit-hooks/

## Description

This manages 3 C/CPP Static Code Analyzers:

- clang-format
- clang-tidy
- oclint

## Usage

Example `.pre-commit-config.yaml` snippet that I use:

```yaml
- repo: https://github.com/pocc/pre-commit-hooks
  sha: master
  hooks:
    - id: clang-format
      args: [-i, --style=Google]
    - id: clang-tidy
      args: [fix, -fix-errors, -checks=*, -warnings-as-errors=*]
    - id: oclint
      args: [-enable-clang-static-analyzer, -enable-global-analysis]
```

Note that you can supply your own args or remove the args line entirely,
depending on your use case.

## Available Hooks

### Prerequisites

_You will need to install these utilities in order to use them._ _Your package
manager may already have them._

- `brew install llvm oclint`
- `apt install clang-format clang-tidy oclint`

### Hook Info

|                                                                          | What it does                                              | Fix Inplace            |
| ------------------------------------------------------------------------ | --------------------------------------------------------- | ---------------------- |
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | Formats C/C++ code according to a style                   | -i                     |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | clang-based C/C++ linter                                  | -fix, --fix-errors [1] |
| [oclint](http://oclint.org/)                                             | static code analysis tool for C, C++ and Objective-C code | N/A                    |

`clang-tidy` is popular and people have written
[additional](https://www.kdab.com/clang-tidy-part-1-modernize-source-code-using-c11c14/)
[articles](https://github.com/KratosMultiphysics/Kratos/wiki/How-to-use-Clang-Tidy-to-automatically-correct-code)
on usage.

[1]: `-fix` will fail if there are compiler errors. `-fix-errors` will `-fix`
and fix compiler errors if it can, like missing semicolons.

### Compilation Database

`clang-tidy` and `oclint` both expect a
[compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html).
Both of the hooks for them will ignore the error for not having one.

You can generate with one `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ...` if you
have a cmake-based project.

### --

Options after `--` like `-std=c++11` will be interpreted correctly for
`clang-tidy` and `oclint`. Make sure they sequentially follow the `--` argument
in the hook's args list.

### Additional Resources

__clang-format__

* This [clang-format
  guide](https://embeddedartistry.com/blog/2017/10/23/creating-and-enforcing-a-coding-standard-with-clang-format):
  is a good overview and a great place to get started
* [clang-format configurator](https://zed0.co.uk/clang-format-configurator/) is
  a website to interactively design your config while [clang-format interactive
  guide](https://clangformat.com/) can help you interactively understand various options
* Everyone has their own take on how to use clang-format, including
  [Mozilla](https://developer.mozilla.org/en-US/docs/Mozilla/Developer_guide/Coding_Style/Formatting_C++_Code_With_clang-format),
  [Apache mesos](http://mesos.apache.org/documentation/latest/clang-format/),
  [Linux
  Kernel](https://www.kernel.org/doc/html/latest/process/clang-format.html), ...
  The options that are available with -style are based on these opinions.

__clang-tidy__

* [clang-tidy
  guide](https://www.kdab.com/clang-tidy-part-1-modernize-source-code-using-c11c14/):
  Good place to start
* [clang-tidy example
  usage](https://github.com/KratosMultiphysics/Kratos/wiki/How-to-use-Clang-Tidy-to-automatically-correct-code):
  Explanation of how to use clang-tidy
* [How to add your own
  checks](https://devblogs.microsoft.com/cppblog/exploring-clang-tooling-part-1-extending-clang-tidy/):
  Function names must be _awesome_!


__oclint__

oclint does not ship with the clang project and is less popular.

* [Using oclint with Fastlane](https://docs.fastlane.tools/actions/oclint/)

## Testing

To run the tests and verify `clang-format`, `clang-tidy`, and `oclint` are
working as expected on your system, use `pytest tests/test.py --runslow`.
