# pre-commit hooks

Designed to be a part of https://pre-commit.com/hooks.html  
Inspired by shell scripts in https://github.com/jumanjihouse/pre-commit-hooks/

## Description

This manages 3 C/CPP Static Code Analyzers:

- clang-format
- clang-tidy
- oclint

It is currently not possible to pass any arguments after `--` 
due to pre-commit architecture.

By default, `-- -DCMAKE_EXPORT_COMPILER_COMMANDS` is added to both 
clang-tidy and oclint to avoid compilation database errors. If you 
want to use a compilation database, reference the command in
`- repo: local` in your config.

## Usage

Add to `.pre-commit-config.yaml` in your git repo:
```yaml
  - repo: https://github.com/pocc/pre-commit-hooks
    sha: master
    hooks:
      - id: clang-format
      - id: clang-tidy
      - id: oclint
```

Add arguments after the id for the utility. clang-format args 
example syntax: `args: [-i, style=Google]`.

## Available Hooks

_You will need to install these utilities to use them._
_Your package manager may already have them._

- `brew install llvm oclint`
- `apt install clang-format clang-tidy oclint`

|                                                                          | What it does                                              | Fix Inplace       |
|--------------------------------------------------------------------------|-----------------------------------------------------------|--------------------|
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | Formats C/C++ code according to a style                   | -i                 |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | clang-based C/C++ linter                                  | -fix, --fix-errors [1] |
| [oclint](http://oclint.org/)                                             | static code analysis tool for C, C++ and Objective-C code | N/A                |

[1]: `-fix` will fail if there are compiler errors vs `-fix-errors` will continue (and can even fix some of them)
