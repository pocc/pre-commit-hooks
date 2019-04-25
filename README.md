# pre-commit hooks

Designed to be a part of https://pre-commit.com/hooks.html. Inspired by shell
scripts in https://github.com/jumanjihouse/pre-commit-hooks/

## Description

This manages 3 C/CPP Static Code Analyzers:

- clang-format
- clang-tidy
- oclint

It is currently not possible to pass any arguments after `--` due to pre-commit
architecture.

## Usage

Example `.pre-commit-config.yaml` snippet that I use:

```yaml
- repo: https://github.com/pocc/pre-commit-hooks
  sha: master
  hooks:
    - id: clang-format
      args: [-i, --style=Google]
    - id: clang-tidy
      args: [-fix-errors, -checks=\*, -warnings-as-errors=\*]
    - id: oclint
      args: [-enable-clang-static-analyzer, -enable-global-analysis]
```

Note that you can supply your own args or remove the args line entirely,
depending on your use case.

## Available Hooks

### Prerequisites

_You will need to install these utilities to use them._ _Your package manager
may already have them._

- `brew install llvm oclint`
- `apt install clang-format clang-tidy oclint`

### Hook Info

|                                                                          | What it does                                              | Fix Inplace            |
| ------------------------------------------------------------------------ | --------------------------------------------------------- | ---------------------- |
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | Formats C/C++ code according to a style                   | -i                     |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | clang-based C/C++ linter                                  | -fix, --fix-errors [1] |
| [oclint](http://oclint.org/)                                             | static code analysis tool for C, C++ and Objective-C code | N/A                    |

[1]: `-fix` will fail if there are compiler errors. `-fix-errors` will `-fix`
and fix compiler errors if it can, like missing semicolons.

### Compilation Database

`clang-tidy` and `oclint` both expect a
[compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html).
Both hooks will ignore the error for not having one.

You can generate with one `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ...` if you
have a cmake-based project.

### --

Options after `--` like `-std=c++11` will be interpreted correctly for
`clang-tidy` and `oclint`. Make sure they sequentially follow the `--` argument
in the hook's args list.

## Testing

To run the tests and verify `clang-format`, `clang-tidy`, and `oclint` are
working as expected on your system, use `pytest tests/test.py --runslow`.
