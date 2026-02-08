# GitHub Issues Summary

**Repository**: pocc/pre-commit-hooks
**Total Issues**: 46
**Open Issues**: 14
**Closed Issues**: 32
**Last Updated**: 2026-02-07

---

## 📊 Statistics

- **Open Rate**: 30.4% (14/46)
- **Oldest Open Issue**: #38 (2021-09-14) - 4+ years old
- **Newest Open Issue**: #67 (2024-06-07)

---

## 🔴 Open Issues (14)

### Issue Categories

#### 🐛 Bugs (5 issues)
1. **#44** - clang-format stops working when using --version (2022-04-06)
   - **Potentially Fixed**: Our --version handling improvements may have addressed this
   - URL: https://github.com/pocc/pre-commit-hooks/issues/44

2. **#45** - oclint multiple execution and inability to see the output (2022-04-14)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/45

3. **#46** - Class ClangTidyCmd disregards its `args` parameter (2022-05-18)
   - **Related to Our Fix**: We fixed a clang-tidy logic error - may be related
   - URL: https://github.com/pocc/pre-commit-hooks/issues/46

4. **#55** - include-what-you-use does not fail (2022-11-25)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/55

5. **#62** - file not found [clang-diagnostic-error] #include "lib1.h" (2023-07-30)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/62

#### ✨ Feature Requests (6 issues)
1. **#38** - Add ability to only lint/analyze committed lines (2021-09-14)
   - **Oldest open issue** - Enhancement request
   - URL: https://github.com/pocc/pre-commit-hooks/issues/38

2. **#48** - Parallelize clang-tidy hook (MISSING from open list - may be PR)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/48

3. **#51** - clang-tidy file exclude pattern ignored (2022-11-01)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/51

4. **#57** - Configurable `uncrustify` executable path (2022-12-23)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/57

5. **#59** - Use a clang-format file that isn't at the root of the repo (2023-03-08)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/59

6. **#67** - Example hook config for vala (2024-06-07)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/67

#### ❓ Questions/Documentation (2 issues)
1. **#53** - LLVM really includes clang-format and clang-tidy? (2022-11-06)
   - Documentation question
   - URL: https://github.com/pocc/pre-commit-hooks/issues/53

2. **#61** - Mistake in comment ? (2023-04-19)
   - **Potentially Fixed**: We fixed several typos and docstring errors
   - URL: https://github.com/pocc/pre-commit-hooks/issues/61

#### 🔧 Configuration Issues (1 issue)
1. **#58** - clang-tidy: for the -p option: may not occur within a group! (2023-03-01)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/58

#### 🔀 Pull Requests (1 issue)
1. **#47** - Changed errant `sys.argv` to `args` parameter passed in (MISSING - likely merged PR)
   - URL: https://github.com/pocc/pre-commit-hooks/issues/47

---

## 🎯 Issues Potentially Fixed by Our Changes

Based on our comprehensive fixes, these issues may now be resolved:

### ✅ Likely Fixed
1. **#44** - clang-format --version issue
   - **Our Fix**: Improved --version argument parsing and handling
   - **Test Coverage**: Added comprehensive --version tests

2. **#46** - ClangTidyCmd args parameter issue
   - **Our Fix**: Fixed critical clang-tidy logic error in args handling
   - **Test Coverage**: Added regression tests for clang-tidy

3. **#61** - Mistake in comment
   - **Our Fix**: Fixed 3 typos in docstrings across utils.py, oclint.py, include_what_you_use.py
   - **Test Coverage**: Added regression tests to prevent typo reintroduction

### ⚠️ Partially Addressed
1. **#66** - Bump black from 19.10b0 to 24.3.0 (appears in open issues count but not list)
   - **Our Fix**: Updated black to 24.10.0 (even newer than requested!)
   - **Status**: Should be closed

---

## 📋 Issues Requiring Investigation

These issues need deeper investigation or may require additional work:

### High Priority (Bugs)
1. **#45** - oclint multiple execution and output visibility
2. **#55** - include-what-you-use does not fail when it should
3. **#62** - file not found errors in clang-tidy

### Medium Priority (Features)
1. **#38** - Lint only committed lines (4+ years old, popular request)
2. **#51** - File exclude patterns
3. **#57** - Configurable executable paths
4. **#59** - Non-root clang-format file support

### Low Priority (Documentation/Examples)
1. **#53** - LLVM documentation clarification
2. **#58** - Configuration help
3. **#67** - Vala example config

---

## 📝 Recommended Next Steps

### Immediate Actions
1. **Test and close potentially fixed issues**:
   - Test #44 (--version handling)
   - Test #46 (clang-tidy args)
   - Close #61 (typos fixed)
   - Close #66 (black updated)

2. **Investigate high-priority bugs**:
   - #45 (oclint output)
   - #55 (include-what-you-use failures)
   - #62 (file not found errors)

### Future Enhancements
1. **Add file exclude pattern support** (#51)
2. **Add configurable executable paths** (#57)
3. **Add non-root .clang-format support** (#59)
4. **Consider parallelization** (#48)
5. **Add Vala examples** (#67)

---

## 📁 Downloaded Files
- `issues_all.json` - All 46 issues with full details
- `issues_open.json` - 14 open issues
- `issues_page1.json` - First page of API results
- `issues_page2.json` - Second page of API results

---

## 🔗 Useful Links
- All Issues: https://github.com/pocc/pre-commit-hooks/issues
- Open Issues: https://github.com/pocc/pre-commit-hooks/issues?q=is%3Aissue+is%3Aopen
- Closed Issues: https://github.com/pocc/pre-commit-hooks/issues?q=is%3Aissue+is%3Aclosed
