# Pre-Commit Hooks Documentation

This directory contains comprehensive documentation for the pre-commit-hooks project, with a focus on cross-platform testing and CI/CD.

## Quick Start

If you're experiencing test failures or setting up CI, start here:

1. **[CROSS_PLATFORM_FIXES.md](CROSS_PLATFORM_FIXES.md)** - Overview of all cross-platform testing fixes
   - Read this first to understand the complete picture
   - Learn about the root cause and key fixes

2. **[TEST_NORMALIZATION.md](TEST_NORMALIZATION.md)** - Patterns for test output normalization
   - Read this when adding new tests or debugging test failures
   - Understand when and how to normalize test output

3. **[MACOS_SDK_SETUP.md](MACOS_SDK_SETUP.md)** - Guide for macOS SDK configuration
   - Read this if you're working with clang-tidy or iwyu on macOS
   - Essential for understanding system header resolution

## Documentation Index

### Cross-Platform Testing

- **[CROSS_PLATFORM_FIXES.md](CROSS_PLATFORM_FIXES.md)**
  - Complete overview of fixes that made all 199 tests pass on Ubuntu, Windows, and macOS
  - Root cause analysis: integration tests using remote v1.3.4 instead of local code
  - Summary of all platform-specific fixes
  - Final results and key learnings

- **[TEST_NORMALIZATION.md](TEST_NORMALIZATION.md)**
  - Detailed patterns for normalizing test output across platforms
  - When to normalize and when NOT to normalize
  - Path separators, line endings, diagnostic names, trailing newlines
  - Platform-specific filtering strategies
  - Return code normalization rules

- **[MACOS_SDK_SETUP.md](MACOS_SDK_SETUP.md)**
  - Step-by-step guide for configuring macOS SDK for clang-tidy and iwyu
  - Environment variables (SDKROOT)
  - Compilation database configuration (-isysroot)
  - Test output filtering for system header noise
  - Common pitfalls and best practices

### Issue-Specific Documentation

- **[ISSUE_36_RESOLUTION.md](ISSUE_36_RESOLUTION.md)**
  - Detailed explanation of issue #36 (CMake integration test)
  - Root cause: missing cmake_minimum_required directive
  - Solution and test structure
  - CMake best practices for compilation databases

### Context and Timeline

- **[CONVERSATION_CONTEXT.md](CONVERSATION_CONTEXT.md)**
  - Complete conversation timeline from 64 test failures to zero
  - Chronological phases of fixes
  - User interactions and questions
  - Files modified and lessons learned
  - Success metrics (135/199 → 199/199 tests passing)

## Common Scenarios

### Scenario: Adding a New Test

1. Read [TEST_NORMALIZATION.md](TEST_NORMALIZATION.md) to understand normalization patterns
2. Use `assert_equal()` from `tests/test_utils.py` for automatic path/line ending normalization
3. Consider platform-specific filtering if your test involves:
   - clang-tidy on macOS (system header filtering)
   - iwyu on macOS (implementation header filtering)
   - Windows-specific diagnostic names

### Scenario: Test Failing on macOS Only

1. Read [MACOS_SDK_SETUP.md](MACOS_SDK_SETUP.md) to understand SDK configuration
2. Check if error involves system headers (paths containing `/MacOSX.sdk/`)
3. Review filtering logic in `tests/test_hooks.py`
4. Ensure SDKROOT is set and `-isysroot` is in compilation database

### Scenario: Test Failing on Windows Only

1. Read [TEST_NORMALIZATION.md](TEST_NORMALIZATION.md) → "Path Separators" section
2. Check for path separator issues (`\` vs `/`)
3. Check for line ending issues (`\r\n` vs `\n`)
4. Check for diagnostic name differences (return-mismatch vs return-type)

### Scenario: Integration Test Not Working

1. Read [CROSS_PLATFORM_FIXES.md](CROSS_PLATFORM_FIXES.md) → "Root Cause Analysis" section
2. Ensure `integration_test()` uses local repository (`repo_root`), not remote
3. Verify `compile_commands.json` is created and staged
4. Check that test expectations match current tool behavior

### Scenario: CMake Integration Issues

1. Read [ISSUE_36_RESOLUTION.md](ISSUE_36_RESOLUTION.md)
2. Ensure `cmake_minimum_required()` is in your CMakeLists.txt
3. Verify `CMAKE_EXPORT_COMPILE_COMMANDS=ON` is set
4. Check that clang-tidy can find the compilation database with `-p=build`

## Testing Commands

```bash
# Run all tests
python3 -m pytest tests/ -vvv

# Run specific test
pytest tests/test_hooks.py::TestHooks::test_run[clang-tidy] -vvv

# Run tests for a specific command
pytest tests/ -k "clang-tidy" -vvv

# Run integration tests only
pytest tests/test_hooks.py -vvv

# Run on all platforms
# Ubuntu/macOS:
python3 -m pytest tests/ -vvv

# Windows:
python -m pytest tests/ -vvv
```

## Contributing

When modifying tests or adding new ones:

1. ✅ Test on all platforms (Ubuntu, Windows, macOS)
2. ✅ Use built-in normalization functions (`assert_equal()`)
3. ✅ Document platform-specific behaviors
4. ✅ Follow selective filtering principles (filter noise, preserve errors)
5. ✅ Update documentation if adding new patterns

## Success Story

This documentation represents the journey from:
- **Before**: 64 test failures on Ubuntu, multiple failures on Windows/macOS
- **After**: ✅ 199/199 tests passing on all platforms

**Total commits**: 25 commits documenting the entire journey
**Key fix**: Integration tests now test local code instead of remote v1.3.4
**Result**: Robust cross-platform test suite with comprehensive documentation

## Questions?

If you have questions not covered by this documentation:
1. Check the conversation context in [CONVERSATION_CONTEXT.md](CONVERSATION_CONTEXT.md)
2. Review the specific documentation file for your scenario
3. Look at the implementation in `tests/test_utils.py` and `tests/test_hooks.py`
4. File an issue on GitHub with details about your specific scenario

## Links

- **Repository**: https://github.com/pocc/pre-commit-hooks
- **GitHub Actions**: See `.github/workflows/` for CI configuration
- **Test Framework**: See `tests/test_utils.py` for integration test infrastructure
- **Main Test Suite**: See `tests/test_hooks.py` for test implementations
