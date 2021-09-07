# pre-commit hooks

![Ubuntu Build](https://github.com/pocc/pre-commit-hooks/actions/workflows/gh_actions_ubuntu.yml/badge.svg)
![Macos Build](https://github.com/pocc/pre-commit-hooks/actions/workflows/gh_actions_macos.yml/badge.svg)
![Windows Build](https://github.com/pocc/pre-commit-hooks/actions/workflows/gh_actions_windows.yml/badge.svg)


This is a [pre-commit](https://pre-commit.com) hooks repo that
integrates two C/C++ code formatters:
> [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html),
[uncrustify](http://uncrustify.sourceforge.net/),

and five C/C++ static code analyzers:
> [clang-tidy](https://clang.llvm.org/extra/clang-tidy/),
[oclint](http://oclint.org/),
[cppcheck](http://cppcheck.sourceforge.net/),
[cpplint](https://github.com/cpplint/cpplint),
[include-what-you-use](https://github.com/include-what-you-use/include-what-you-use)

This repo's hooks do more than passthrough arguments to provide these features:

* Relay correct pass/fail to pre-commit, even when some commands exit 0 when they should not. Some versions of oclint, clang-tidy, and cppcheck have this behavior.
* Honor `--` arguments, which pre-commit [has problems with](https://github.com/pre-commit/pre-commit/issues/1000)
* Optionally [enforce a command version](https://github.com/pocc/pre-commit-hooks#enforcing-linter-version-with---version) so your team gets code formatted/analyzed the same way
* Formatters clang-format and uncrustify will error with diffs of what has changed

## Example Usage

With this err.c

```cpp
#include <string>
int main(){int i;return;}
```

All seven linters should fail on commit
and produce [this output](tests/test_repo/test_integration_expected_stderr.txt)

<details>
  <summary>Pre-commit linters image output</summary>
    <p align="center">
      <img src="media/clinters_err.png" width="80%">
    </p>
</details>

using this `.pre-commit-config.yaml`:

```yaml
fail_fast: false
repos:
  - repo: https://github.com/pocc/pre-commit-hooks
    rev: master
    hooks:
      - id: clang-format
        args: [--style=Google]
      - id: clang-tidy
      - id: oclint
      - id: uncrustify
      - id: cppcheck
      - id: cpplint
      - id: iwyu
```

_Note that for your config yaml, you can supply your own args or remove the args line entirely,
depending on your use case._

You can also clone this repo and then run the test_repo to see all of the linters at work,

```bash
git clone https://github.com/pocc/pre-commit-hooks
cd tests/test_repo
git init
pre-commit install
git add .
git commit
```

## Using this repo

### Special flags in this repo

There are 2 flags, `--version` and `--no-diff` that can be added to `args:` for a pre-commit hook.
They will be removed and not be passed on to the command.

Some linters change behavior between versions. To enforce a linter version
8.0.0, for example, add `--version=8.0.0` to `args:` for that linter. Note that
this is a pre-commit hook arg and will be filtered before args are passed to the linter.

You can add `--no-diff` to the `args:` for clang-format and uncrustify
if you would like there to be no diff output for these commands.

### Default Options

These options are automatically added to enable all errors or are required.

* oclint: `["-enable-global-analysis", "-enable-clang-static-analyzer", "-max-priority-3", "0"]`
* uncrustify: `["-c", "defaults.cfg", "-q"]` (options added, and a defaults.cfg generated, if -c is missing)
* cppcheck: `["-q" , "--error-exitcode=1", "--enable=all", "--suppress=unmatchedSuppression", "--suppress=missingIncludeSystem", "--suppress=unusedFunction"]` (See https://github.com/pocc/pre-commit-hooks/pull/30)
* cpplint: `["--verbose=0"]`

If any of these options are supplied in `args:`, they will override the above defaults.

### Compilation Database

`clang-tidy` and `oclint` both expect a
[compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html).
Both of the hooks for them will ignore the error for not having one.

You can generate with one `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON ...` if you
have a cmake-based project.

## Information about the Commands

Python3.6+ is required to use these hooks as all 5 invoking scripts are written in it.
As this is also the minimum version of pre-commit, this should not be an issue.

### Installation

_You will need to install these utilities in order to use them. Your package
manager may already have them. Below are the package names for each package manager, if available:_

- `apt install clang clang-format clang-tidy uncrustify cppcheck iwyu` [1] [2]
- `yum install llvm uncrustify cppcheck iwyu` [2]
- `brew install llvm oclint uncrustify cppcheck include-what-you-use` [3]
- `choco install llvm uncrustify cppcheck inlcude-what-you-use` [4]

cpplint can be installed everywhere with `pip install cpplint`.

[1]: `clang` is a required install for `clang-format` or `clang-tidy` to work.

[2]: oclint takes a couple hours to compile. I've compiled and tarred
[oclint-v0.15](https://dl.dropboxusercontent.com/s/nu474emafxj2nn5/oclint.tar.gz)
for those using linux who want to skip the wait (built on Ubuntu-18.04).
You can also download the older [oclint-v0.13.1](https://github.com/oclint/oclint/releases/download/v0.13.1/oclint-0.13.1-x86_64-linux-4.4.0-112-generic.tar.gz)
for linux from oclint's github page (see [releases](https://github.com/oclint/oclint/releases)).

[3]: Depending on your brew installation, you may need to install
oclint with `brew cask install oclint`.

[4]: oclint is not available on windows.

If your package manager is not listed here, it will have similar names for these tools.
You can build all of these from source.

### Hook Info

| Hook Info                                                                | Type                 | Languages                             |
| ------------------------------------------------------------------------ | -------------------- | ------------------------------------- |
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | Formatter            | C, C++, ObjC, ObjC++, Java            |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | Static code analyzer | C, C++, ObjC                          |
| [oclint](http://oclint.org/)                                             | Static code analyzer | C, C++, ObjC                          |
| [uncrustify](http://uncrustify.sourceforge.net/)                         | Formatter            | C, C++, C#, ObjC, D, Java, Pawn, Vala |
| [cppcheck](http://cppcheck.sourceforge.net/)                             | Static code analyzer | C, C++                                |
| [cpplint](https://github.com/cpplint/cpplint)                            | Style checker        | C, C++                                |
| [include-what-you-use](https://github.com/include-what-you-use/include-what-you-use) | Static code analyzer | C, C++                    |

### Hook Option Comparison

| Hook Options                                                             | Fix In Place | Enable all Checks                             | Set key/value |
| ------------------------------------------------------------------------ | ------------ | --------------------------------------------- | --------------- |
| [clang-format](https://clang.llvm.org/docs/ClangFormatStyleOptions.html) | `-i`         |                   | |
| [clang-tidy](https://clang.llvm.org/extra/clang-tidy/)                   | `--fix-errors` [1] | `-checks=*` `-warnings-as-errors=*` [2] | |
| [oclint](http://oclint.org/)                                             |  | `-enable-global-analysis` `-enable-clang-static-analyzer` `-max-priority-3 0` [3] | `-rc=<key>=<value>` |
| [uncrustify](http://uncrustify.sourceforge.net/)                         | `--replace` `--no-backup` [4] |  | `--set key=value` |
| [cppcheck](http://cppcheck.sourceforge.net/)                             |  | `-enable=all` | |
| [cpplint](https://github.com/cpplint/cpplint)                            |  | `--verbose=0` |  |
| [include-what-you-use](https://github.com/include-what-you-use/include-what-you-use) | | `--verbose=3` | |


[1]: `-fix` will fail if there are compiler errors. `-fix-errors` will `-fix`
and fix compiler errors if it can, like missing semicolons.

[2]: Be careful with `-checks=*`.  can have self-contradictory rules in newer versions of llvm (9+):
modernize wants to use [trailing return type](https://clang.llvm.org/extra/clang-tidy/checks/modernize-use-trailing-return-type.html)
but Fuchsia [disallows it](https://clang.llvm.org/extra/clang-tidy/checks/fuchsia-trailing-return.html).
*Thanks to @rambo.*

[3]: The oclint pre-commit hook does the equivalent of `-max-priority-3 0` by default, which returns an error code when any check fails.
See [oclint error codes](https://docs.oclint.org/en/stable/manual/oclint.html#exit-status-options) for more info on partially catching failed checks.

[4]: By definition, if you are using `pre-commit`, you are using version control.
Therefore, it is recommended to avoid needless backup creation by using `--no-backup`.

## Development

See [README_dev.md](README_dev.md)

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
