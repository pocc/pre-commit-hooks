# macOS SDK Setup Guide for clang-tidy and iwyu

## Problem Statement

On macOS, clang-tidy and include-what-you-use (iwyu) require proper configuration to find system headers (like `<stdio.h>`, `<iostream>`, etc.). Without this configuration, you'll see errors like:

```
error: 'stdio.h' file not found
error: no member named 'cout' in namespace 'std'
```

Additionally, clang-tidy may generate hundreds of warnings from system headers in the macOS SDK, cluttering test output and causing false failures.

## Solution Components

The solution requires **three coordinated changes**:

### 1. Environment Variable in CI (GitHub Actions)

Set `SDKROOT` to point to the macOS SDK path:

```yaml
# .github/workflows/gh_actions_macos.yml
- name: Configure macOS SDK for clang-tidy
  run: |
    echo "SDKROOT=$(xcrun --show-sdk-path)" >> $GITHUB_ENV
```

**What it does**:
- `xcrun --show-sdk-path` returns the path to the active macOS SDK (e.g., `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX15.2.sdk`)
- Setting `SDKROOT` tells clang tools where to find system headers

**What NOT to do**:
- Don't set `CPATH` - it can cause header resolution conflicts
- Don't hardcode the SDK path - use `xcrun --show-sdk-path` for portability

### 2. Compilation Database Configuration

Add `-isysroot` flag to the clang command in `compile_commands.json`:

```python
# tests/test_utils.py
def set_compilation_db(filenames):
    """Create a compilation database for clang static analyzers."""
    cdb = "["
    clang_location = shutil.which("clang")
    file_dir = os.path.dirname(os.path.abspath(filenames[0]))

    # On macOS, get SDK path for proper system header resolution
    sdk_flags = ""
    if sys.platform == "darwin":
        sdk_path_result = sp.run(["xcrun", "--show-sdk-path"], stdout=sp.PIPE, stderr=sp.PIPE)
        if sdk_path_result.returncode == 0:
            sdk_path = sdk_path_result.stdout.decode().strip()
            sdk_flags = f" -isysroot {sdk_path}"

    for f in filenames:
        file_base = os.path.basename(f)
        clang_suffix = ""
        if f.endswith("cpp"):
            clang_suffix = "++"
        cdb += """\n{{
    "directory": "{0}",
    "command": "{1}{2} {3}{4} -o {3}.o",
    "file": "{3}"
}},""".format(
            file_dir, clang_location, clang_suffix, os.path.join(file_dir, file_base), sdk_flags
        )
    cdb = cdb[:-1] + "]"  # Remove trailing comma and close JSON

    with open(os.path.join(file_dir, "compile_commands.json"), "w") as f:
        f.write(cdb)
```

**What it does**:
- Adds `-isysroot /path/to/sdk` to each compilation command
- This tells clang exactly where to find system headers
- Works in conjunction with `SDKROOT` environment variable

**Example output** in `compile_commands.json`:
```json
[{
    "directory": "/tmp/test",
    "command": "/usr/bin/clang ok.c -isysroot /Applications/Xcode.app/.../MacOSX15.2.sdk -o ok.c.o",
    "file": "/tmp/test/ok.c"
}]
```

### 3. Test Output Filtering

Even with proper SDK configuration, clang-tidy may generate warnings/errors from system headers. These need to be filtered to avoid false test failures:

```python
# tests/test_hooks.py
if cmd_name == "clang-tidy":
    # Filter warnings/errors count
    before_filter = actual
    filtered_actual = re.sub(rb"\d+ warnings? generated\.\n", b"", actual)
    # Also filter combined pattern like "148 warnings and 1 error generated."
    filtered_actual = re.sub(rb"\d+ warnings? and \d+ errors? generated\.\n",
                            lambda m: re.sub(rb"\d+ warnings? and ", b"", m.group(0)),
                            filtered_actual)
    filtered_warnings_count = (filtered_actual != before_filter)

    # Filter errors from macOS SDK system headers
    lines = filtered_actual.split(b"\n")
    has_test_file_errors = any(
        b"/test_repo/" in l and b": error:" in l and b"/MacOSX.sdk/" not in l
        for l in lines
    )

    # Keep errors from test files, filter system header errors
    filtered_lines = []
    filtered_system_headers = filtered_warnings_count
    skip_next = False
    for i, line in enumerate(lines):
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

    # Normalize return code when we filtered system headers and result matches expected
    if filtered_system_headers and sp_child.returncode == 1:
        if actual.strip() == target_output.strip() and target_output.strip() == b"":
            sp_child = sp.CompletedProcess(
                sp_child.args, 0, sp_child.stdout, sp_child.stderr
            )
```

**What it does**:
- Removes "X warnings generated." and "X warnings and Y errors generated." lines
- Filters out errors/warnings from paths containing `/MacOSX.sdk/`
- Removes associated "Error while processing" and "note:" lines
- **Preserves** errors from actual test files (containing `/test_repo/`)
- Normalizes return code to 0 when only system header errors were filtered

**Key design principle**: **Selective filtering** - only filter system header noise, never filter legitimate errors from test files.

## include-what-you-use (iwyu) on macOS

iwyu has an additional quirk on macOS: it suggests including C++ standard library implementation headers (starting with `__`):

```
ok.cpp should add these lines:
#include <__ostream/basic_ostream.h>  // for operator<<, basic_ostream
```

These suggestions are incorrect - users should include `<iostream>`, not `<__ostream/basic_ostream.h>`.

**Filter implementation**:
```python
if cmd_name == "include-what-you-use" and sys.platform == "darwin":
    lines = actual.split(b"\n")
    in_add_section = False
    add_section_headers = []
    for line in lines:
        if b"should add these lines:" in line:
            in_add_section = True
        elif b"should remove these lines:" in line or b"The full include-list" in line:
            in_add_section = False
        elif in_add_section and line.strip().startswith(b"#include"):
            add_section_headers.append(line)

    # If all "add" suggestions are for implementation headers, filter entire output
    if add_section_headers and all(b"<__" in h for h in add_section_headers):
        actual = b""
        # Normalize return code since we filtered the suggestions
        if sp_child.returncode == 1 and target_output.strip() == b"":
            sp_child = sp.CompletedProcess(
                sp_child.args, 0, sp_child.stdout, sp_child.stderr
            )
```

**What it does**:
- Parses iwyu output to extract "should add these lines:" suggestions
- Checks if all suggestions are for implementation headers (containing `<__`)
- If so, filters the entire output and normalizes return code to 0

## Verification

To verify the setup works:

```bash
# Check SDK path
xcrun --show-sdk-path
# Should output something like: /Applications/Xcode.app/.../MacOSX15.2.sdk

# Check clang can find headers with -isysroot
echo '#include <stdio.h>' | clang -x c -isysroot $(xcrun --show-sdk-path) -fsyntax-only -
# Should have no output (success)

# Run tests
python3 -m pytest tests/ -k "clang-tidy or iwyu"
```

## Common Pitfalls

### ❌ Don't: Set CPATH environment variable
```yaml
# DON'T DO THIS
- name: Configure macOS SDK
  run: |
    echo "CPATH=$(xcrun --show-sdk-path)/usr/include" >> $GITHUB_ENV
```
**Why not**: Can cause header resolution conflicts and unexpected behavior.

### ❌ Don't: Hardcode SDK paths
```python
# DON'T DO THIS
sdk_flags = " -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.0.sdk"
```
**Why not**: SDK versions change with Xcode updates. Use `xcrun --show-sdk-path` for portability.

### ❌ Don't: Filter all errors
```python
# DON'T DO THIS
if b": error:" in line:
    continue  # Skip all errors
```
**Why not**: Will hide legitimate errors from test files. Only filter system header errors.

### ❌ Don't: Always normalize return codes
```python
# DON'T DO THIS
if sp_child.returncode == 1:
    sp_child = sp.CompletedProcess(sp_child.args, 0, ...)  # Always normalize to 0
```
**Why not**: Only normalize when filtered output matches expected empty output.

## Summary

✅ **Do**:
1. Set `SDKROOT` environment variable in CI
2. Add `-isysroot` to compilation database
3. Filter system header errors selectively
4. Preserve test file errors
5. Normalize return codes only when appropriate
6. Use `xcrun --show-sdk-path` for SDK path detection

✅ **Result**: All clang-tidy and iwyu tests pass on macOS without false failures from system headers.

## Related Documentation

- [Cross-Platform Testing Fixes](CROSS_PLATFORM_FIXES.md)
- [Test Normalization Patterns](TEST_NORMALIZATION.md)
- [Apple Documentation: Using the SDK](https://developer.apple.com/documentation/xcode/configuring-your-project-to-use-sdks)
