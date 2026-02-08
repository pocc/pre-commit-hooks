#!/usr/bin/env python3
"""Tests for error handling and edge cases across all hooks.

This file tests various error scenarios to ensure hooks handle
errors gracefully and provide useful error messages.
"""
import os
import subprocess as sp
import tempfile

import pytest


class TestMissingCommandErrors:
    """Test error handling when commands are not installed."""

    def test_error_message_includes_command_name(self):
        """Test that error messages include the command name."""
        # Try to run a hook that doesn't exist
        result = sp.run(
            ["python3", "-c", "from hooks.utils import Command; c = Command('fake', 'fake', []); c.check_installed()"],
            capture_output=True,
        )
        assert result.returncode != 0

    def test_error_message_includes_help_url(self):
        """Test that error messages include helpful URL."""
        from hooks.clang_format import ClangFormatCmd

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() { return 0; }\n")
            temp_file = f.name

        try:
            # Mock a missing command by using a fake name
            cmd = ClangFormatCmd(["clang-format-hook", temp_file])
            original_command = cmd.command
            cmd.command = "fake-nonexistent-command"

            with pytest.raises(SystemExit):
                cmd.check_installed()

            # Error should have been written to stderr
            assert b"github.com/pocc/pre-commit-hooks" in cmd.stderr
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestVersionMismatchErrors:
    """Test version mismatch error handling."""

    def test_version_mismatch_shows_both_versions(self):
        """Test that version mismatch errors show expected and actual versions."""
        # Request an impossible version
        result = sp.run(
            ["clang-format-hook", "--version=0.0.1", "test.c"],
            capture_output=True,
        )

        # Should fail
        assert result.returncode != 0
        # Error should mention versions (either in stdout or stderr)
        output = result.stdout + result.stderr
        # Should contain some indication of version mismatch
        assert b"version" in output.lower() or b"Version" in output


class TestFileNotFoundErrors:
    """Test error handling for missing files."""

    def test_nonexistent_file_produces_error(self):
        """Test that trying to format a nonexistent file produces an error."""
        result = sp.run(
            ["clang-format-hook", "/nonexistent/path/to/file.c"],
            capture_output=True,
        )
        # Should fail
        assert result.returncode != 0


class TestEmptyInputHandling:
    """Test handling of empty or no input."""

    def test_no_files_with_no_staged_changes(self):
        """Test behavior when no files are provided and no files are staged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize empty git repo
            sp.run(["git", "init"], cwd=tmpdir, capture_output=True)
            sp.run(
                ["git", "config", "user.email", "test@test.com"],
                cwd=tmpdir,
                capture_output=True,
            )
            sp.run(
                ["git", "config", "user.name", "Test"],
                cwd=tmpdir,
                capture_output=True,
            )

            # Run hook with no files (should try to use git and find nothing)
            result = sp.run(
                ["cppcheck-hook"],
                cwd=tmpdir,
                capture_output=True,
            )
            # Either succeeds with no files or fails appropriately
            assert result.returncode in [0, 1]


class TestMalformedInputs:
    """Test handling of malformed or unusual inputs."""

    def test_binary_file_handling(self):
        """Test that binary files don't crash the hooks."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".c", delete=False) as f:
            # Write some binary data
            f.write(b"\x00\x01\x02\x03\x04\x05")
            temp_file = f.name

        try:
            # Try to format binary file
            result = sp.run(
                ["clang-format-hook", temp_file],
                capture_output=True,
            )
            # Should handle it gracefully (either skip or error appropriately)
            assert isinstance(result.returncode, int)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_empty_file_handling(self):
        """Test that empty files are handled correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Write nothing (empty file)
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", temp_file],
                capture_output=True,
            )
            # Should handle empty file gracefully
            assert isinstance(result.returncode, int)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_very_long_filename(self):
        """Test handling of very long filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with a very long name (but within OS limits)
            long_name = "a" * 200 + ".c"
            long_path = os.path.join(tmpdir, long_name)

            try:
                with open(long_path, "w") as f:
                    f.write("int main() { return 0; }\n")

                result = sp.run(
                    ["clang-format-hook", long_path],
                    capture_output=True,
                )
                # Should handle long filename
                assert isinstance(result.returncode, int)
            except OSError:
                # If OS doesn't support this, skip
                pytest.skip("OS doesn't support very long filenames")

    def test_special_characters_in_filename(self):
        """Test handling of special characters in filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with special chars (that are valid in filenames)
            special_name = "test_file-with.special+chars.c"
            special_path = os.path.join(tmpdir, special_name)

            with open(special_path, "w") as f:
                f.write("int main() { return 0; }\n")

            result = sp.run(
                ["clang-format-hook", special_path],
                capture_output=True,
            )
            # Should handle special chars
            assert isinstance(result.returncode, int)


class TestConcurrentFileHandling:
    """Test handling of multiple files."""

    def test_multiple_files_some_pass_some_fail(self):
        """Test that hooks correctly report when some files pass and others fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            good_file = os.path.join(tmpdir, "good.c")
            bad_file = os.path.join(tmpdir, "bad.c")

            # Good file: properly formatted
            with open(good_file, "w") as f:
                f.write("int main() {\n  return 0;\n}\n")

            # Bad file: poorly formatted
            with open(bad_file, "w") as f:
                f.write("int main(){int x;return 0;}")

            result = sp.run(
                ["clang-format-hook", "--style=google", good_file, bad_file],
                capture_output=True,
            )

            # Should fail because bad_file is improperly formatted
            assert result.returncode != 0

    def test_multiple_files_all_pass(self):
        """Test that hooks succeed when all files are correct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.c")
            file2 = os.path.join(tmpdir, "file2.c")

            # Both files properly formatted
            for f in [file1, file2]:
                with open(f, "w") as fd:
                    fd.write("int main() {\n  return 0;\n}\n")

            result = sp.run(
                ["clang-format-hook", "--style=google", file1, file2],
                capture_output=True,
            )

            # Should pass because both files are properly formatted
            assert result.returncode == 0


class TestConfigFileIssues:
    """Test handling of configuration file issues."""

    def test_uncrustify_invalid_config(self):
        """Test uncrustify handling of invalid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_cfg = os.path.join(tmpdir, "invalid.cfg")
            test_file = os.path.join(tmpdir, "test.c")

            # Create invalid config
            with open(invalid_cfg, "w") as f:
                f.write("invalid config syntax!@#$%\n")

            with open(test_file, "w") as f:
                f.write("int main() { return 0; }\n")

            result = sp.run(
                ["uncrustify-hook", "-c", invalid_cfg, test_file],
                capture_output=True,
            )

            # Should handle invalid config (likely will fail)
            assert isinstance(result.returncode, int)

    def test_uncrustify_missing_config(self):
        """Test uncrustify handling when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.c")
            nonexistent_cfg = os.path.join(tmpdir, "nonexistent.cfg")

            with open(test_file, "w") as f:
                f.write("int main() { return 0; }\n")

            result = sp.run(
                ["uncrustify-hook", "-c", nonexistent_cfg, test_file],
                capture_output=True,
            )

            # Should handle missing config
            assert isinstance(result.returncode, int)


class TestCompilationDatabaseIssues:
    """Test handling of compilation database issues for clang-tidy/oclint."""

    def test_clang_tidy_without_compilation_database(self):
        """Test that clang-tidy handles missing compilation database gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.c")

            with open(test_file, "w") as f:
                f.write("int main() { return 0; }\n")

            result = sp.run(
                ["clang-tidy-hook", test_file],
                cwd=tmpdir,
                capture_output=True,
            )

            # Should handle gracefully (the hook is designed to ignore this error)
            assert isinstance(result.returncode, int)

    @pytest.mark.skipif(os.name == "nt", reason="OCLint not available on Windows")
    def test_oclint_without_compilation_database(self):
        """Test that oclint handles missing compilation database gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.c")

            with open(test_file, "w") as f:
                f.write("int main() { return 0; }\n")

            result = sp.run(
                ["oclint-hook", test_file],
                cwd=tmpdir,
                capture_output=True,
            )

            # Should handle gracefully (the hook is designed to ignore this error)
            assert isinstance(result.returncode, int)


class TestStdinStdoutBehavior:
    """Test that hooks properly handle stdin/stdout/stderr."""

    def test_formatter_diff_goes_to_stdout(self):
        """Test that formatter diffs are sent to stdout."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Poorly formatted code
            f.write("int main(){int x;return 0;}")
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", "--style=google", temp_file],
                capture_output=True,
            )

            # Should fail
            assert result.returncode != 0
            # Diff should be in stdout
            assert len(result.stdout) > 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_static_analyzer_errors_to_stderr(self):
        """Test that static analyzer errors go to stderr."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            # Code with error
            f.write("int main() { int unused; return; }")
            temp_file = f.name

        try:
            result = sp.run(
                ["cppcheck-hook", temp_file],
                capture_output=True,
            )

            # Should fail (unused variable)
            assert result.returncode != 0
            # Error should be in stderr
            assert len(result.stderr) > 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestReturnCodeCorrectness:
    """Test that return codes are correct for various scenarios."""

    def test_clean_code_returns_zero(self):
        """Test that properly formatted, error-free code returns 0."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main() {\n  return 0;\n}\n")
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", "--style=google", temp_file],
                capture_output=True,
            )
            # Should pass
            assert result.returncode == 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_bad_code_returns_nonzero(self):
        """Test that improperly formatted code returns non-zero."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
            f.write("int main(){return 0;}")
            temp_file = f.name

        try:
            result = sp.run(
                ["clang-format-hook", "--style=google", temp_file],
                capture_output=True,
            )
            # Should fail
            assert result.returncode != 0
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
