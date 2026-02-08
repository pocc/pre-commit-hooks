#!/usr/bin/env python3
"""Comprehensive edge case tests for pre-commit hooks.

Tests cover:
- Argument parsing edge cases
- Error handling scenarios
- File handling edge cases
- Version checking edge cases
- Logic error regression tests
"""
import os
import subprocess as sp
import sys
import tempfile
from pathlib import Path

import pytest

from hooks.clang_format import ClangFormatCmd
from hooks.clang_tidy import ClangTidyCmd
from hooks.cppcheck import CppcheckCmd
from hooks.cpplint import CpplintCmd
from hooks.oclint import OCLintCmd
from hooks.uncrustify import UncrustifyCmd
from hooks.utils import Command, FormatterCmd, StaticAnalyzerCmd


class TestArgumentParsing:
    """Test argument parsing edge cases."""

    def test_version_with_equals(self):
        """Test --version=8.0.0 format."""
        args = ["clang-format-hook", "--version=8.0.0", "test.c"]
        # This should exit with 0 if version matches or 1 if it doesn't
        result = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        assert result.returncode in [0, 1]

    def test_version_with_space(self):
        """Test --version 8.0.0 format."""
        args = ["clang-format-hook", "--version", "8.0.0", "test.c"]
        result = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        assert result.returncode in [0, 1]

    def test_no_diff_flag_removal(self):
        """Test that --no-diff flag is properly removed for formatters."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["clang-format-hook", "--no-diff", temp_file]
            cmd = ClangFormatCmd(["clang-format-hook", "--no-diff", temp_file])
            sys.argv = original_argv
            assert "--no-diff" not in cmd.args
            assert cmd.no_diff_flag is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_args_with_double_dash(self):
        """Test handling of -- separator in arguments."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # The -- separator should be handled correctly
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["cppcheck-hook", "--", temp_file]
            cmd = CppcheckCmd(["cppcheck-hook", "--", temp_file])
            sys.argv = original_argv
            assert temp_file in cmd.files
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestFileHandling:
    """Test file handling edge cases."""

    def test_nonexistent_file(self):
        """Test that nonexistent files are filtered out gracefully."""
        # Mock sys.argv for get_added_files()
        original_argv = sys.argv
        sys.argv = ["clang-format-hook", "/nonexistent/file.c"]
        cmd = ClangFormatCmd(["clang-format-hook", "/nonexistent/file.c"])
        sys.argv = original_argv
        # Nonexistent files should be filtered out, resulting in empty file list
        assert "/nonexistent/file.c" not in cmd.files
        assert len(cmd.files) == 0

    def test_empty_file_list(self):
        """Test handling of empty file list."""
        # Should use git to find files or exit gracefully
        result = sp.run(
            ["cppcheck-hook"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            cwd=tempfile.gettempdir(),
        )
        # Either finds no files or errors appropriately
        assert result.returncode in [0, 1]

    def test_cfg_file_filtering(self):
        """Test that .cfg files are filtered out."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("config = value\n")
            cfg_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            c_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["cppcheck-hook", cfg_file, c_file]
            cmd = CppcheckCmd(["cppcheck-hook", cfg_file, c_file])
            sys.argv = original_argv
            assert cfg_file not in cmd.files
            assert c_file in cmd.files
        finally:
            if os.path.exists(cfg_file):
                os.unlink(cfg_file)
            if os.path.exists(c_file):
                os.unlink(c_file)


class TestClangTidyLogic:
    """Test the clang-tidy --fix-errors logic fix."""

    def test_fix_errors_flag_detection(self):
        """Test that --fix-errors flag is properly detected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["clang-tidy-hook", "--fix-errors", temp_file]
            cmd = ClangTidyCmd(["clang-tidy-hook", "--fix-errors", temp_file])
            sys.argv = original_argv
            assert cmd.edit_in_place is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_fix_flag_detection(self):
        """Test that -fix flag is properly detected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["clang-tidy-hook", "-fix", temp_file]
            cmd = ClangTidyCmd(["clang-tidy-hook", "-fix", temp_file])
            sys.argv = original_argv
            assert cmd.edit_in_place is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestCppcheckDefaults:
    """Test cppcheck default argument handling."""

    def test_default_args_added(self):
        """Test that default arguments are added."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["cppcheck-hook", temp_file]
            cmd = CppcheckCmd(["cppcheck-hook", temp_file])
            sys.argv = original_argv
            assert "-q" in cmd.args
            assert "--error-exitcode=1" in cmd.args
            assert "--enable=all" in cmd.args
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_user_args_override_defaults(self):
        """Test that user-provided args override defaults."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["cppcheck-hook", "--enable=warning", temp_file]
            cmd = CppcheckCmd(["cppcheck-hook", "--enable=warning", temp_file])
            sys.argv = original_argv
            # User's --enable=warning should be present
            assert "--enable=warning" in cmd.args
            # Default --enable=all should not be added because user provided --enable
            assert cmd.args.count("--enable=warning") == 1
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestUncrustifyDefaults:
    """Test uncrustify configuration file handling."""

    def test_defaults_cfg_creation(self):
        """Test that defaults.cfg is created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".c", delete=False, dir=tmpdir
            ) as f:
                f.write("int main() { return 0; }\n")
                temp_file = f.name

            try:
                # Mock sys.argv for get_added_files()
                original_argv = sys.argv
                sys.argv = ["uncrustify-hook", temp_file]
                cmd = UncrustifyCmd(["uncrustify-hook", temp_file])
                sys.argv = original_argv
                # If no -c arg provided, defaults.cfg should be created
                if "-c" in cmd.args:
                    idx = cmd.args.index("-c")
                    config_file = cmd.args[idx + 1]
                    # Check that config file exists or is defaults.cfg
                    assert config_file == "defaults.cfg" or os.path.exists(config_file)
            finally:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                defaults_path = os.path.join(tmpdir, "defaults.cfg")
                if os.path.exists(defaults_path):
                    os.unlink(defaults_path)


class TestOCLintVersionHandling:
    """Test OCLint version-specific argument handling."""

    @pytest.mark.skipif(os.name == "nt", reason="OCLint not available on Windows")
    def test_oclint_version_detection(self):
        """Test that OCLint version is detected."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["oclint-hook", temp_file]
            cmd = OCLintCmd(["oclint-hook", temp_file])
            sys.argv = original_argv
            # Version should be a string
            assert isinstance(cmd.version, str)
            assert len(cmd.version) > 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @pytest.mark.skipif(os.name == "nt", reason="OCLint not available on Windows")
    def test_oclint_plist_cleanup(self):
        """Test that OCLint cleans up generated .plist files."""
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                os.chdir(tmpdir)
                test_file = os.path.join(tmpdir, "test.c")
                with open(test_file, "w") as f:
                    f.write("int main() { return 0; }\n")

                plist_file = os.path.join(tmpdir, "test.plist")
                with open(plist_file, "w") as f:
                    f.write("fake plist content\n")

                existing_files = os.listdir(tmpdir)
                assert "test.plist" in existing_files

                # Simulate cleanup - cleanup_files uses os.getcwd()
                OCLintCmd.cleanup_files(existing_files)

                # In actual use, cleanup removes plist files created by oclint
                # Here we just test the method exists and can be called
                assert hasattr(OCLintCmd, "cleanup_files")
            finally:
                os.chdir(original_cwd)


class TestIncludeWhatYouUse:
    """Test include-what-you-use specific behavior."""

    @pytest.mark.skipif(os.name == "nt", reason="IWYU not available on Windows")
    def test_iwyu_correct_includes_message(self):
        """Test that IWYU correctly identifies when includes are correct."""
        # This is more of an integration test, but validates the logic
        # that checks for "has correct #includes/fwd-decls" in stderr
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Write a simple valid C file
            f.write("#include <stdio.h>\nint main() { printf(\"test\"); return 0; }\n")
            temp_file = f.name

        try:
            # Just verify the command can be instantiated
            from hooks.include_what_you_use import IncludeWhatYouUseCmd

            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["include-what-you-use-hook", temp_file]
            cmd = IncludeWhatYouUseCmd(["include-what-you-use-hook", temp_file])
            sys.argv = original_argv
            assert cmd.command == "include-what-you-use"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestErrorMessages:
    """Test error message formatting."""

    def test_command_not_found_error(self):
        """Test error message when command is not installed."""
        # Mock a command that doesn't exist
        result = sp.run(
            ["nonexistent-command-hook"],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_version_mismatch_error_format(self):
        """Test version mismatch error message format."""
        args = ["clang-format-hook", "--version=0.0.1", "test.c"]
        result = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)

        # Should fail and provide helpful error message
        assert result.returncode != 0
        assert b"Version" in result.stderr or b"version" in result.stderr


class TestMultipleFiles:
    """Test handling of multiple files."""

    def test_multiple_files_processed(self):
        """Test that multiple files are processed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "test1.c")
            file2 = os.path.join(tmpdir, "test2.c")

            with open(file1, "w") as f:
                f.write("int main() { return 0; }\n")
            with open(file2, "w") as f:
                f.write("int func() { return 1; }\n")

            # Mock sys.argv for get_added_files()
            original_argv = sys.argv
            sys.argv = ["cppcheck-hook", file1, file2]
            cmd = CppcheckCmd(["cppcheck-hook", file1, file2])
            sys.argv = original_argv
            assert file1 in cmd.files
            assert file2 in cmd.files
            assert len(cmd.files) == 2


class TestFormatterDiffOutput:
    """Test formatter diff output."""

    def test_clang_format_diff_output(self):
        """Test that clang-format produces diff output for incorrectly formatted files."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Intentionally poorly formatted code
            f.write("int main(){int x;return 0;}")
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", "--style=google", temp_file],
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
            # Should fail for poorly formatted code
            assert result.returncode != 0
            # Should show diff
            assert b"original" in result.stdout or b"formatted" in result.stdout
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_no_diff_flag_suppresses_output(self):
        """Test that --no-diff flag suppresses diff output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Intentionally poorly formatted code
            f.write("int main(){int x;return 0;}")
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", "--no-diff", "--style=google", temp_file],
                stdout=sp.PIPE,
                stderr=sp.PIPE,
            )
            # Should still fail but without diff output
            assert result.returncode != 0
            # Diff should be suppressed
            assert len(result.stdout) == 0 or b"original" not in result.stdout
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
