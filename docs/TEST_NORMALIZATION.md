# Test Normalization Patterns

## Overview

This document describes the normalization and filtering patterns used to make tests pass consistently across Ubuntu, Windows, and macOS platforms.

## Core Principle

**Normalize platform-specific differences while preserving test validity.**

Tests should:
- ✅ Pass on all platforms when the underlying functionality is correct
- ✅ Fail on all platforms when there's a real bug
- ❌ Never hide real errors through overly aggressive filtering
- ❌ Never fail due to platform-specific output variations

## Normalization Categories

### 1. Path Separators

**Problem**: Windows uses backslashes (`\`), Unix uses forward slashes (`/`).

**Solution**: Normalize all paths to forward slashes in `assert_equal()`:

```python
def assert_equal(expected: bytes, actual: bytes):
    # Normalize path separators for cross-platform compatibility
    actual = actual.replace(b"\\", b"/")
    expected = expected.replace(b"\\", b"/")
```

**Example**:
```
Windows:  C:\Users\test\file.c
Normalized: C:/Users/test/file.c
Linux:    /home/test/file.c (unchanged)
```

**When to apply**: Always, in the base assertion function.

### 2. Line Endings

**Problem**: Windows uses `\r\n` (CRLF), Unix uses `\n` (LF).

**Solution**: Strip `\r` characters:

```python
def assert_equal(expected: bytes, actual: bytes):
    actual = actual.replace(b"\r", b"")  # ignore windows file ending differences
```

**When to apply**: Always, in the base assertion function.

### 3. Trailing Newlines

**Problem**: Different tools add different numbers of trailing newlines, especially on Windows (cppcheck).

**Solution**: Normalize to exactly one trailing newline:

```python
def assert_equal(expected: bytes, actual: bytes):
    # Normalize trailing newlines to handle platform differences
    if actual and actual.strip() and expected and expected.strip():
        if b"\n" in actual or b"\n" in expected:
            actual = actual.rstrip(b"\n") + b"\n"
            expected = expected.rstrip(b"\n") + b"\n"
```

**When to apply**: Always, in the base assertion function.

### 4. Diagnostic Names (Windows clang)

**Problem**: Windows clang uses different diagnostic names than Linux/macOS.

**Examples**:
- Windows: `clang-diagnostic-return-mismatch` → Linux/macOS: `clang-diagnostic-return-type`
- Windows: `-Wreturn-mismatch` → Linux/macOS: `-Wreturn-type`

**Solution**: Normalize to the Linux/macOS names:

```python
# In run_shell_cmd() and run_integration_test()
actual = actual.replace(b"clang-diagnostic-return-mismatch", b"clang-diagnostic-return-type")
actual = actual.replace(b"-Wreturn-mismatch", b"-Wreturn-type")
```

**When to apply**: In test execution functions, before comparing output.

## Platform-Specific Filtering

### macOS: clang-tidy System Header Noise

**Problem**: Even with proper SDK configuration, clang-tidy generates warnings/errors from macOS SDK system headers.

**Example**:
```
/Applications/Xcode.app/.../MacOSX.sdk/usr/include/_stdio.h:123:4: error: ...
148 warnings and 1 error generated.
Error while processing /tmp/test/ok.c.
```

**Solution**: Multi-stage selective filtering:

#### Stage 1: Filter warning/error counts
```python
# Filter "X warnings generated." and "X warnings and Y errors generated."
filtered_actual = re.sub(rb"\d+ warnings? generated\.\n", b"", actual)
filtered_actual = re.sub(rb"\d+ warnings? and \d+ errors? generated\.\n",
                        lambda m: re.sub(rb"\d+ warnings? and ", b"", m.group(0)),
                        filtered_actual)
```

#### Stage 2: Filter system header errors while preserving test file errors
```python
# Detect if there are errors from actual test files
has_test_file_errors = any(
    b"/test_repo/" in l and b": error:" in l and b"/MacOSX.sdk/" not in l
    for l in lines
)

filtered_lines = []
filtered_system_headers = filtered_warnings_count
skip_next = False

for line in lines:
    # Filter SDK system header errors
    if b"/MacOSX.sdk/" in line and (b": error:" in line or b": warning:" in line):
        filtered_system_headers = True
        skip_next = True
        continue

    # Filter "Error while processing" only if preceded by SDK errors
    if b"Error while processing" in line and filtered_system_headers:
        continue

    # Skip note/help lines after filtered errors
    if skip_next and (b": note:" in line or line.strip().startswith(b"^")):
        continue

    skip_next = False
    filtered_lines.append(line)

actual = b"\n".join(filtered_lines)
```

#### Stage 3: Normalize return code conditionally
```python
# Only normalize if:
# 1. We filtered system headers
# 2. Return code is 1 (error)
# 3. Filtered output matches expected empty output
if filtered_system_headers and sp_child.returncode == 1:
    if actual.strip() == target_output.strip() and target_output.strip() == b"":
        sp_child = sp.CompletedProcess(
            sp_child.args, 0, sp_child.stdout, sp_child.stderr
        )
```

**Key design decisions**:
- ✅ Filter system header errors from `/MacOSX.sdk/` paths
- ✅ Filter "Error while processing" only when preceded by SDK errors
- ✅ Filter associated "note:" and "^" lines
- ❌ **Never** filter errors from `/test_repo/` paths (actual test files)
- ❌ **Never** normalize return code when test file has real errors

**Why it works**: Distinguishes between "clang-tidy found SDK header issues" (noise) and "clang-tidy found issues in test code" (real errors).

### macOS: iwyu Implementation Header Suggestions

**Problem**: iwyu on macOS suggests including C++ standard library implementation headers (starting with `__`):

```
ok.cpp should add these lines:
#include <__ostream/basic_ostream.h>  // for operator<<, basic_ostream

ok.cpp should remove these lines:
- #include <iostream>  // lines 2-2
```

This is incorrect - users should include `<iostream>`, not `<__ostream/basic_ostream.h>`.

**Solution**: Filter entire output when all suggestions are implementation headers:

```python
if cmd_name == "include-what-you-use" and sys.platform == "darwin":
    lines = actual.split(b"\n")
    in_add_section = False
    add_section_headers = []

    # Parse "should add these lines:" section
    for line in lines:
        if b"should add these lines:" in line:
            in_add_section = True
        elif b"should remove these lines:" in line or b"The full include-list" in line:
            in_add_section = False
        elif in_add_section and line.strip().startswith(b"#include"):
            add_section_headers.append(line)

    # If all "add" suggestions are for implementation headers (containing <__), filter entire output
    if add_section_headers and all(b"<__" in h for h in add_section_headers):
        actual = b""
        # Normalize return code since we filtered the suggestions
        if sp_child.returncode == 1 and target_output.strip() == b"":
            sp_child = sp.CompletedProcess(
                sp_child.args, 0, sp_child.stdout, sp_child.stderr
            )
```

**Key design decisions**:
- Only filter when **all** suggestions are implementation headers (`<__`)
- If there's a mix of implementation and public headers, **don't filter**
- Normalize return code when filtering complete output

**Why it works**: Allows legitimate iwyu suggestions while filtering macOS-specific implementation header noise.

## Return Code Normalization Rules

Return code normalization is **conditional** and **conservative**:

### When to Normalize

✅ **Do normalize** (exit code 1 → 0) when **all** of these are true:
1. We filtered platform-specific output (system headers, implementation headers, etc.)
2. Tool returned exit code 1
3. Filtered output matches expected output
4. Expected output is empty

```python
if filtered_something and sp_child.returncode == 1:
    if actual.strip() == target_output.strip() and target_output.strip() == b"":
        sp_child = sp.CompletedProcess(sp_child.args, 0, ...)
```

### When NOT to Normalize

❌ **Don't normalize** when:
- Test file has real errors (even if system headers also have errors)
- Expected output is non-empty
- We didn't filter anything
- Tool returned exit code 0 or other codes
- Filtered output doesn't match expected output

**Example: Real error in test file**
```python
# Test file err.c has: int main(){int i;return;}
# clang-tidy output: error: non-void function 'main' should return a value
# Even if system headers also have errors, DON'T normalize because test file has error
if has_test_file_errors:
    # Don't normalize - this is a real failure
    pass
```

## Test File Text Mode vs Binary Mode

**Problem**: Windows text mode converts `\n` to `\r\n` when writing files, breaking tests.

**Solution**: Use binary mode for test files:

```python
# tests/test_utils_functions.py
def test_get_filelines():
    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:  # Use "wb" not "w"
        f.write(b"line1\nline2\nline3\n")
    # ... rest of test
```

**When to apply**: Any test that writes files and checks their exact content.

## Pre-commit Info/Warning Line Filtering

**Problem**: Pre-commit outputs `[INFO]` and `[WARNING]` lines during first run:
```
[INFO] Initializing environment for ...
[INFO] Installing environment for ...
[WARNING] The 'rev' field of repo ...
```

**Solution**: Filter these lines from integration test output:

```python
# tests/test_utils.py
def integration_test(cmd_name, files, args, test_dir):
    sp_child = sp.run(["pre-commit", "run"], cwd=test_dir, stdout=sp.PIPE, stderr=sp.PIPE)
    output_actual = sp_child.stderr + sp_child.stdout
    # Get rid of pre-commit first run info lines
    output_actual = re.sub(rb"\[(?:INFO|WARNING)\].*\n", b"", output_actual)
```

**When to apply**: Always in integration_test function.

## Version-Specific Output Handling

**Problem**: Tool output changes between versions (e.g., clang-tidy --fix-errors behavior).

**Solution**: Update test expectations to match current tool behavior:

```json
// tests/table_tests_integration.json
// Old expectation (clang-tidy < 14):
{
  "expd_output": "clang-tidy...Failed\nerr.c:2:27: error: non-void function...",
  "expd_retcode": 1
}

// New expectation (clang-tidy >= 14 with --fix-errors):
{
  "expd_output": "clang-tidy...Passed\n",
  "expd_retcode": 0
}
```

**When to apply**: When tool behavior changes in a way that's correct but different.

## Testing the Normalizations

### Verify Cross-Platform Behavior

```bash
# On Linux/macOS
python3 -m pytest tests/ -vvv

# On Windows
python -m pytest tests/ -vvv

# Run specific test on all platforms
pytest tests/test_hooks.py::TestHooks::test_run[clang-tidy]
```

### Debug Normalization Issues

Add debug output to see what's being filtered:

```python
def assert_equal(expected: bytes, actual: bytes):
    # Add before normalization
    print(f"\n\nBefore normalization:")
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")

    # ... normalization code ...

    # Add after normalization
    print(f"\n\nAfter normalization:")
    print(f"Expected: {expected}")
    print(f"Actual: {actual}")
```

## Summary

### Always Apply (Base Normalization)
1. ✅ Convert Windows `\` to `/` for paths
2. ✅ Remove `\r` characters (Windows line endings)
3. ✅ Normalize trailing newlines

### Conditionally Apply (Platform-Specific)
4. ✅ Windows: Normalize clang diagnostic names
5. ✅ macOS: Filter system header errors (clang-tidy)
6. ✅ macOS: Filter implementation header suggestions (iwyu)
7. ✅ macOS: Normalize return codes when appropriate

### Never Do
- ❌ Filter errors from actual test files
- ❌ Normalize return codes unconditionally
- ❌ Hide real failures through aggressive filtering

## Related Documentation

- [Cross-Platform Testing Fixes](CROSS_PLATFORM_FIXES.md)
- [macOS SDK Setup Guide](MACOS_SDK_SETUP.md)
