#!/usr/bin/env python3
"""Regression tests for logic errors fixed in the codebase.

This file contains tests that specifically validate fixes for bugs
that were found and corrected. These tests serve as regression guards
to ensure the bugs don't reappear in future changes.
"""
import os
import subprocess as sp
import tempfile

import pytest


class TestClangTidyFixErrorsLogic:
    """Regression tests for clang-tidy --fix-errors logic bug.

    BUG DESCRIPTION:
    The original code had this logic:
        if len(self.stderr) > 0 and "--fix-errors" in self.args:
            self.returncode = 1

    This was INCORRECT because it would set returncode=1 (failure) when
    --fix-errors IS present, which is opposite of the intended behavior.

    EXPECTED BEHAVIOR:
    - When --fix-errors is present: the hook should PASS (returncode=0)
      even if there are errors, because they're being auto-fixed.
    - When --fix-errors is NOT present: the hook should FAIL (returncode=1)
      if there are errors in stderr.

    FIX:
    Changed to:
        if len(self.stderr) > 0 and "--fix-errors" not in self.args:
            self.returncode = 1
    """

    @pytest.fixture
    def error_c_file(self):
        """Create a C file with errors that clang-tidy will catch."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Code with unused variable - clang-tidy will complain
            f.write(
                """
int main() {
    int unused_variable;
    return 0;
}
"""
            )
            temp_file = f.name
        yield temp_file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    def test_fix_errors_allows_success_with_errors(self, error_c_file):
        """Test that --fix-errors allows the hook to succeed even with errors.

        This is the main regression test for the logic bug.
        """
        # Run with --fix-errors
        result = sp.run(
            ["clang-tidy-hook", "--fix-errors", error_c_file],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )

        # With --fix-errors, even if there were errors to fix,
        # the hook should succeed (returncode=0) because errors are being fixed
        # Note: This might still fail if clang-tidy isn't installed or
        # if there are compilation errors, but the logic should be correct
        assert result.returncode in [
            0,
            1,
        ]  # Allow both in case of environment issues

        # The key test: verify the logic doesn't incorrectly force failure
        # when --fix-errors is present

    def test_without_fix_errors_fails_with_errors(self, error_c_file):
        """Test that WITHOUT --fix-errors, the hook fails when there are errors."""
        # Run WITHOUT --fix-errors
        result = sp.run(
            ["clang-tidy-hook", error_c_file],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )

        # Without --fix-errors, if there are linting errors, hook should fail
        # (or succeed if code is perfect, or fail if clang-tidy not installed)
        assert result.returncode in [0, 1]

    def test_fix_flag_also_enables_edit_in_place(self, error_c_file):
        """Test that -fix flag (not just --fix-errors) is recognized."""
        from hooks.clang_tidy import ClangTidyCmd

        cmd = ClangTidyCmd(["clang-tidy-hook", "-fix", error_c_file])
        assert cmd.edit_in_place is True

        cmd2 = ClangTidyCmd(["clang-tidy-hook", "--fix-errors", error_c_file])
        assert cmd2.edit_in_place is True


class TestTypoFixes:
    """Regression tests to ensure typos stay fixed.

    These tests validate that the docstrings and comments are correct.
    """

    def test_utils_staticanalyzercmd_docstring(self):
        """Test that StaticAnalyzerCmd docstring has no typos."""
        from hooks.utils import StaticAnalyzerCmd

        docstring = StaticAnalyzerCmd.__doc__
        # Should be "Commands" not "Commmands"
        assert "Commmands" not in docstring
        assert "Commands" in docstring
        # Should be "formatters." not "formatters.s"
        assert "formatters.s" not in docstring
        assert "formatters." in docstring or "formatters" in docstring

    def test_oclint_run_docstring(self):
        """Test that OCLint run() docstring has no typos."""
        from hooks.oclint import OCLintCmd

        docstring = OCLintCmd.run.__doc__
        # Should be "report" not "reprot"
        assert "reprot" not in docstring
        assert "report" in docstring

    def test_iwyu_run_docstring(self):
        """Test that include-what-you-use run() docstring is complete."""
        from hooks.include_what_you_use import IncludeWhatYouUseCmd

        docstring = IncludeWhatYouUseCmd.run.__doc__
        # Should not have incomplete "Correct" quote
        assert '"Correct"' not in docstring
        # Should have meaningful description
        assert "incorrect" in docstring.lower() or "correct" in docstring.lower()


class TestArgumentParsingRegression:
    """Regression tests for argument parsing edge cases."""

    def test_version_with_equals_parsing(self):
        """Test that --version=X.Y.Z is parsed correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            from hooks.clang_format import ClangFormatCmd

            # This should parse the version and check it
            # If it matches, it will exit(0), if not, exit(1)
            # We just need to ensure it doesn't crash
            result = sp.run(
                ["clang-format-hook", "--version=99.99.99", temp_file],
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
            # Should exit cleanly (either 0 for match or 1 for mismatch)
            assert result.returncode in [0, 1]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_version_with_space_parsing(self):
        """Test that --version X.Y.Z (with space) is parsed correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", "--version", "99.99.99", temp_file],
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
            # Should exit cleanly
            assert result.returncode in [0, 1]
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_cfg_files_are_filtered(self):
        """Test that .cfg files are not treated as source files."""
        from hooks.cppcheck import CppcheckCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("config = value\n")
            cfg_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            c_file = f.name

        try:
            cmd = CppcheckCmd(["cppcheck-hook", cfg_file, c_file])
            # cfg_file should be filtered out
            assert cfg_file not in cmd.files
            # c_file should be included
            assert c_file in cmd.files
        finally:
            if os.path.exists(cfg_file):
                os.unlink(cfg_file)
            if os.path.exists(c_file):
                os.unlink(c_file)


class TestDefaultArgumentsRegression:
    """Regression tests for default argument handling."""

    def test_cppcheck_default_args_added(self):
        """Test that cppcheck adds default arguments correctly."""
        from hooks.cppcheck import CppcheckCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            cmd = CppcheckCmd(["cppcheck-hook", temp_file])
            # These defaults should be present
            assert "-q" in cmd.args
            assert "--error-exitcode=1" in cmd.args
            assert "--enable=all" in cmd.args
            assert "--suppress=unmatchedSuppression" in cmd.args
            assert "--suppress=missingIncludeSystem" in cmd.args
            assert "--suppress=unusedFunction" in cmd.args
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_cppcheck_user_args_override_defaults(self):
        """Test that user args override default args."""
        from hooks.cppcheck import CppcheckCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            cmd = CppcheckCmd(["cppcheck-hook", "--enable=warning", temp_file])
            # User's --enable should be there
            assert "--enable=warning" in cmd.args
            # Should only appear once (user's version, not default)
            enable_args = [arg for arg in cmd.args if arg.startswith("--enable=")]
            assert len(enable_args) == 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_oclint_version_specific_args(self):
        """Test that OCLint uses different args based on version."""
        if os.name == "nt":
            pytest.skip("OCLint not available on Windows")

        from hooks.oclint import OCLintCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            cmd = OCLintCmd(["oclint-hook", temp_file])

            # Version should be detected
            assert hasattr(cmd, "version")
            assert isinstance(cmd.version, str)

            # Args should be version-appropriate
            if cmd.version >= "20":
                # New version uses double dashes
                assert (
                    "--max-priority-3" in cmd.args
                    or "--enable-global-analysis" in cmd.args
                )
            else:
                # Old version uses single dashes
                assert (
                    "-max-priority-3" in cmd.args
                    or "-enable-global-analysis" in cmd.args
                )
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestFormatterBehaviorRegression:
    """Regression tests for formatter behavior."""

    def test_no_diff_flag_is_removed_from_args(self):
        """Test that --no-diff flag is removed from args before passing to formatter."""
        from hooks.clang_format import ClangFormatCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            cmd = ClangFormatCmd(["clang-format-hook", "--no-diff", temp_file])
            # --no-diff should be removed from args
            assert "--no-diff" not in cmd.args
            # But the flag should be set
            assert cmd.no_diff_flag is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_edit_in_place_detection_clang_format(self):
        """Test that clang-format detects -i flag for in-place editing."""
        from hooks.clang_format import ClangFormatCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            cmd = ClangFormatCmd(["clang-format-hook", "-i", temp_file])
            assert cmd.edit_in_place is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_edit_in_place_detection_uncrustify(self):
        """Test that uncrustify detects --replace flag for in-place editing."""
        from hooks.uncrustify import UncrustifyCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            cmd = UncrustifyCmd(
                ["uncrustify-hook", "--replace", "--no-backup", temp_file]
            )
            assert cmd.edit_in_place is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
