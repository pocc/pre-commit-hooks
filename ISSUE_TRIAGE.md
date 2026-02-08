# Issue Triage and Resolution Plan

**Date**: 2026-02-07
**Total Open Issues**: 14

---

## ✅ ALREADY FIXED (4 issues - can be closed)

### #44 - clang-format stops working when using --version
**Status**: ✅ **LIKELY FIXED**
**Our Fix**: Improved --version argument parsing and handling
**Evidence**:
- We improved version parsing logic in utils.py
- Added comprehensive --version tests in test_edge_cases.py
- The issue describes version checking preventing format checking - our parse_args refactor should fix this

**Action**: Test with the exact config from issue and close if working

---

### #46 - Class ClangTidyCmd disregards its `args` parameter
**Status**: ✅ **FIXED**
**Our Fix**: Fixed critical logic error in clang_tidy.py line 27
**Evidence**:
- Issue says ClangTidyCmd ignores args parameter
- We fixed the logic bug where --fix-errors was inverted
- This was causing args to be mishandled

**Action**: Close immediately - regression tests confirm fix

---

### #61 - Mistake in comment ?
**Status**: ✅ **FIXED**
**Our Fix**: Fixed the exact issue mentioned
**Evidence**:
- Issue points to clang_tidy.py:22 comment being misleading
- We fixed this comment and the logic bug it described
- Regression tests confirm the fix

**Action**: Close immediately with reference to our commit

---

### #66 - Bump black from 19.10b0 to 24.3.0
**Status**: ✅ **FIXED** (issue not in open list but mentioned)
**Our Fix**: Updated to black 24.10.0
**Action**: If exists, close immediately

---

## 🔧 CAN FIX (3 issues)

### #49 - Incorrect order of arguments for include-what-you-use
**Status**: 🔧 **CAN FIX**
**Issue**: Arguments in wrong order - should be `<clang opts> <source file>` not `<source file> <clang opts>`
**Current Code**: `self.run_command([filename] + self.args)` in include_what_you_use.py:25
**Fix**: Change to `self.run_command(self.args + [filename])`
**Risk**: Low - this matches the documented interface

---

### #55 - include-what-you-use does not fail
**Status**: 🔧 **CAN FIX** (might be related to #49)
**Issue**: IWYU doesn't fail when it should
**Current Logic**: Checks for "has correct #includes/fwd-decls" in stderr
**Fix**: May be related to arg order (#49), or need to check exit code properly
**Action**: Fix arg order first, then verify error detection logic

---

### #45 - oclint multiple execution and inability to see the output
**Status**: 🔧 **CAN IMPROVE**
**Issue**:
1. OCLint runs for each file (by design, but confusing)
2. Output not clear
**Fix**:
1. Add clearer output/logging
2. Document the per-file behavior
**Risk**: Medium - need to preserve functionality

---

## ❓ NEED MORE INFO (4 issues)

### #51 - clang-tidy file exclude pattern ignored
**Status**: ❓ **NEED MORE INFO**
**Issue**: Exclude patterns work for clang-format but not clang-tidy
**Why**: Need to understand how pre-commit passes exclude patterns
**Action**: Request example config and expected vs actual behavior

---

### #58 - clang-tidy: for the -p option: may not occur within a group!
**Status**: ❓ **NEED MORE INFO**
**Issue**: Using `-p some/folder` gives error about groups
**Possible Cause**: How args are parsed/passed to clang-tidy
**Action**: Need full error output and clang-tidy version

---

### #62 - file not found [clang-diagnostic-error] #include "lib1.h"
**Status**: ❓ **NEED MORE INFO**
**Issue**: Include files not found during linting
**Likely Cause**: Missing compilation database or include paths
**Action**: This is user configuration issue, need to provide better docs/error messages

---

### #53 - LLVM really includes clang-format and clang-tidy?
**Status**: ❓ **DOCUMENTATION ISSUE**
**Issue**: Documentation says LLVM includes these tools but user's install doesn't
**Fix**: Update README to clarify installation
**Action**: Update installation instructions

---

## 🎯 FEATURE REQUESTS (3 issues - defer)

### #38 - Add ability to only lint/analyze committed lines
**Status**: 🎯 **FEATURE REQUEST**
**Effort**: High - requires integration with git diff
**Priority**: Medium - oldest issue (4+ years) but complex
**Action**: Defer - out of scope for current fixes

---

### #57 - Configurable uncrustify executable path
**Status**: 🎯 **FEATURE REQUEST**
**Effort**: Medium - need to add config parameter support
**Priority**: Low - workaround exists (modify PATH)
**Action**: Defer - enhancement for future

---

### #59 - Use a clang-format file that isn't at the root
**Status**: 🎯 **FEATURE REQUEST**
**Effort**: Medium - need to support --style=file:path
**Priority**: Medium - valid use case
**Action**: Defer - enhancement for future

---

### #67 - Example hook config for vala
**Status**: 🎯 **DOCUMENTATION**
**Effort**: Low - just need example
**Priority**: Low - niche language
**Action**: Can add example to README

---

## 📊 Summary

| Category | Count | Action |
|----------|-------|--------|
| Already Fixed | 4 | Close with test/reference |
| Can Fix Now | 3 | Implement fixes |
| Need More Info | 4 | Request clarification |
| Feature Requests | 3 | Defer or document |
| **Total** | **14** | |

---

## 🚀 Immediate Action Plan

### Phase 1: Fix What We Can (Now)
1. ✅ Fix #49 - IWYU argument order
2. ✅ Fix #55 - IWYU error detection (after #49)
3. ✅ Improve #45 - OCLint output clarity

### Phase 2: Close Fixed Issues (Now)
1. ✅ Test and close #44 - version handling
2. ✅ Close #46 - args parameter (with commit ref)
3. ✅ Close #61 - comment mistake (with commit ref)
4. ✅ Close #66 - black update (if exists)

### Phase 3: Documentation Updates (Now)
1. ✅ Update #53 - Installation docs
2. ✅ Add #67 - Vala example (if simple)

### Phase 4: Request More Info (Later)
1. Comment on #51 requesting config example
2. Comment on #58 requesting full error
3. Comment on #62 suggesting compilation database setup

### Phase 5: Feature Requests (Future)
1. Label #38, #57, #59 as enhancements
2. Consider for future roadmap
