"""Tests for security module."""

import os
import tempfile

import pytest

from y2tmp3.security import (
    sanitize_filename,
    secure_path_join,
    validate_output_directory,
    validate_youtube_url,
)


class TestSanitizeFilename:
    """Test filename sanitization."""

    def test_basic_filename(self):
        """Test basic filename sanitization."""
        result = sanitize_filename("Hello World")
        assert result == "Hello World"

    def test_dangerous_characters(self):
        """Test removal of dangerous characters."""
        result = sanitize_filename('file<>:"|?*name')
        assert result == "filename"

    def test_path_traversal_attempt(self):
        """Test prevention of path traversal."""
        result = sanitize_filename("../../../etc/passwd")
        assert result == "passwd"  # Only basename remains after sanitization
        assert ".." not in result
        assert "/" not in result

    def test_null_bytes(self):
        """Test removal of null bytes."""
        result = sanitize_filename("file\x00name")
        assert result == "filename"

    def test_multiple_dots(self):
        """Test handling of multiple dots."""
        result = sanitize_filename("file...txt")
        assert result == "file.txt"

    def test_reserved_windows_names(self):
        """Test handling of reserved Windows filenames."""
        result = sanitize_filename("CON")
        assert result == "download_CON"

        result = sanitize_filename("PRN.txt")
        assert result == "download_PRN.txt"

    def test_empty_filename(self):
        """Test handling of empty filename."""
        result = sanitize_filename("")
        assert result == "download"

        result = sanitize_filename("...")
        assert result == "download"

    def test_long_filename(self):
        """Test handling of very long filenames."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 200

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        result = sanitize_filename("café")
        assert result == "cafe"  # Unicode normalized and non-ASCII chars handled


class TestValidateYouTubeUrl:
    """Test YouTube URL validation."""

    def test_valid_youtube_urls(self):
        """Test valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ",
        ]
        for url in valid_urls:
            assert validate_youtube_url(url), f"URL should be valid: {url}"

    def test_invalid_youtube_urls(self):
        """Test invalid YouTube URLs."""
        invalid_urls = [
            "https://example.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch",  # No video ID
            "https://www.youtube.com/watch?v=",  # Empty video ID
            "https://youtu.be/",  # No video ID
            "not_a_url",
            "",
            None,
            123,
            "javascript:alert('xss')",
            "file:///etc/passwd",
        ]
        for url in invalid_urls:
            assert not validate_youtube_url(url), f"URL should be invalid: {url}"

    def test_malicious_urls(self):
        """Test rejection of malicious URLs."""
        malicious_urls = [
            "https://evil.com/youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ",
            "ftp://youtube.com/watch?v=dQw4w9WgXcQ",
        ]
        for url in malicious_urls:
            assert not validate_youtube_url(url), (
                f"Malicious URL should be rejected: {url}"
            )


class TestSecurePathJoin:
    """Test secure path joining."""

    def test_normal_path_join(self):
        """Test normal path joining."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = secure_path_join(tmpdir, "subdir", "file.txt")
            expected = os.path.join(tmpdir, "subdir", "file.txt")
            assert result == expected

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Path traversal attempt detected"):
                secure_path_join(tmpdir, "..", "etc", "passwd")

            with pytest.raises(ValueError, match="Path traversal attempt detected"):
                secure_path_join(tmpdir, "subdir", "..", "..", "etc", "passwd")

    def test_absolute_path_in_components(self):
        """Test handling of absolute paths in components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Path traversal attempt detected"):
                secure_path_join(tmpdir, "/etc/passwd")


class TestValidateOutputDirectory:
    """Test output directory validation."""

    def test_valid_directory(self):
        """Test validation of valid directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert validate_output_directory(tmpdir)

    def test_nonexistent_directory(self):
        """Test rejection of nonexistent directory."""
        assert not validate_output_directory("/nonexistent/directory")

    def test_file_instead_of_directory(self):
        """Test rejection of file path instead of directory."""
        with tempfile.NamedTemporaryFile() as tmpfile:
            assert not validate_output_directory(tmpfile.name)

    def test_empty_path(self):
        """Test rejection of empty path."""
        assert not validate_output_directory("")
        assert not validate_output_directory(None)

    def test_sensitive_directories(self):
        """Test rejection of sensitive system directories."""
        sensitive_dirs = ["/etc", "/bin", "/sbin", "/usr/bin", "/root"]
        for directory in sensitive_dirs:
            if os.path.exists(directory):
                assert not validate_output_directory(directory), (
                    f"Should reject sensitive dir: {directory}"
                )

    def test_readonly_directory(self):
        """Test rejection of read-only directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Make directory read-only
            os.chmod(tmpdir, 0o444)
            try:
                assert not validate_output_directory(tmpdir)
            finally:
                # Restore permissions for cleanup
                os.chmod(tmpdir, 0o755)
