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
* Optionally [enforce a command version](https://github.com/pocc/pre-commit-hooks#special-flags-in-this-repo) so your team gets code formatted/analyzed the same way
* Formatters clang-format and uncrustify will error with diffs of what has changed

## Example Usage

With this [err.c](tests/test_repo/err.c)

```c
#include <stdio.h>
int main(){int i;return;}
```

and using this `.pre-commit-config.yaml`:

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
      - id: include-what-you-use
```

All seven linters should fail on commit with these messages.
Full text is at [media/all_failed.txt](media/all_failed.txt).

<details>
  <summary>clang-format error (indentation)</summary>

```
clang-format.............................................................Failed
- hook id: clang-format
- exit code: 1

err.c
====================
--- original

+++ formatted

@@ -1,3 +1,6 @@

 #include <stdio.h>
-int main(){int i;return;}
+int main() {
+  int i;
+  return;
+}

```
</details>
<details>
  <summary>clang-tidy error (non-void main should return a value)</summary>

```
clang-tidy...............................................................Failed
- hook id: clang-tidy
- exit code: 1

/tmp/temp/err.c:2:18: error: non-void function 'main' should return a value [clang-diagnostic-return-type]
int main(){int i;return;}
                 ^
1 error generated.
Error while processing /tmp/temp/err.c.
Found compiler error(s).

```
</details>
<details>
  <summary>oclint error (non-void main should return a value)</summary>

```
oclint...................................................................Failed
- hook id: oclint
- exit code: 6

Compiler Errors:
(please be aware that these errors will prevent OCLint from analyzing this source code)

/tmp/temp/err.c:2:18: non-void function 'main' should return a value

Clang Static Analyzer Results:

/tmp/temp/err.c:2:18: non-void function 'main' should return a value


OCLint Report

Summary: TotalFiles=0 FilesWithViolations=0 P1=0 P2=0 P3=0


[OCLint (https://oclint.org) v21.05]

```
</details>
<details>
  <summary>uncrustify error (indentation)</summary>

```
uncrustify...............................................................Failed
- hook id: uncrustify
- exit code: 1

err.c
====================
--- original

+++ formatted

@@ -1,3 +1,5 @@

 #include <stdio.h>
-int main(){int i;return;}
+int main(){
+  int i; return;
+}

```
</details>
<details>
  <summary>cppcheck error (unused variable i)</summary>

```
cppcheck.................................................................Failed
- hook id: cppcheck
- exit code: 1

err.c:2:16: style: Unused variable: i [unusedVariable]
int main(){int i;return;}
               ^

```
</details>
<details>
  <summary>cpplint error (no copyright message, bad whitespace)</summary>

```
cpplint..................................................................Failed
- hook id: cpplint
- exit code: 1

Done processing err.c
Total errors found: 4
err.c:0:  No copyright message found.  You should have a line: "Copyright [year] <Copyright Owner>"  [legal/copyright] [5]
err.c:2:  More than one command on the same line  [whitespace/newline] [0]
err.c:2:  Missing space after ;  [whitespace/semicolon] [3]
err.c:2:  Missing space before {  [whitespace/braces] [5]

```
</details>
<details>
  <summary>include-what-you-use error (remove unused #include <stdio.h>)</summary>

```
include-what-you-use.....................................................Failed
- hook id: include-what-you-use
- exit code: 3

err.c:2:18: error: non-void function 'main' should return a value [-Wreturn-type]
int main(){int i;return;}
                 ^

err.c should add these lines:

err.c should remove these lines:
- #include <stdio.h>  // lines 1-1

The full include-list for err.c:
---

```
</details>

_Note that for your config yaml, you can supply your own args or remove the args line entirely,
depending on your use case._

You can also clone this repo and then run the test_repo to see all of the linters at work to produce this output,

```bash
git clone https://github.com/pocc/pre-commit-hooks
cd pre-commit-hooks/tests/test_repo
git init
pre-commit install
pre-commit run
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

If any of these options are supplied in `args:`, they will override the above defaults (use `-<flag>=<option>` if possible when overriding).

### Compilation Database

`clang-tidy` and `oclint` both expect a
[compilation database](https://clang.llvm.org/docs/JSONCompilationDatabase.html).
Both of the hooks for them will ignore the error for not having one.

You can generate with one `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON <dir>` if you
have a cmake-based project.

## Information about the Commands

Python3.6+ is required to use these hooks as all 5 invoking scripts are written in it.
As this is also the minimum version of pre-commit, this should not be an issue.

### Installation

_You will need to install these utilities in order to use them. Your package
manager may already have them. Below are the package names for each package manager, if available:_

* `apt install clang clang-format clang-tidy uncrustify cppcheck iwyu` [1] [2]
* `yum install llvm uncrustify cppcheck iwyu` [2]
* `brew install llvm oclint uncrustify cppcheck include-what-you-use` [3]
* `choco install llvm uncrustify cppcheck inlcude-what-you-use` [4]
* `pipx install clang-format` or `pip install clang-format` [5]

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

[5]: Only supplies the `clang-format` hook requirement. Can be pinned to a specific release.
    
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
* [clang-format Options Explorer](https://zed0.co.uk/clang-format-configurator/) - Website to interactively
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

### cpplint

* [Google C++ style guide (basis of cpplint)](https://google.github.io/styleguide/cppguide.html)
* [Source Code](https://github.com/cpplint/cpplint)

### include-what-you-use

* [Official Docs](https://include-what-you-use.org/)
* [Using include-what-you-use](https://www.incredibuild.com/blog/include-what-you-use-how-to-best-utilize-this-tool-and-avoid-common-issues)
* [Source Code](https://github.com/include-what-you-use/include-what-you-use)

## License

Apache 2.0
