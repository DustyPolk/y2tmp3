"""Tests for utils module."""

import subprocess
from unittest.mock import MagicMock, patch

from y2tmp3.utils import check_ffmpeg_installed


class TestCheckFfmpegInstalled:
    """Test ffmpeg installation check."""

    @patch("shutil.which")
    def test_ffmpeg_found_by_which(self, mock_which):
        """Test ffmpeg found by shutil.which."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        assert check_ffmpeg_installed() is True
        mock_which.assert_called_once_with("ffmpeg")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_found_by_subprocess(self, mock_run, mock_which):
        """Test ffmpeg found by subprocess when which fails."""
        mock_which.return_value = None
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert check_ffmpeg_installed() is True

        mock_which.assert_called_once_with("ffmpeg")
        mock_run.assert_called_once_with(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=5,
            check=False,
        )

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_not_found(self, mock_run, mock_which):
        """Test ffmpeg not found."""
        mock_which.return_value = None
        mock_run.side_effect = FileNotFoundError()

        assert check_ffmpeg_installed() is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_subprocess_fails(self, mock_run, mock_which):
        """Test ffmpeg subprocess returns non-zero exit code."""
        mock_which.return_value = None
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        assert check_ffmpeg_installed() is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_subprocess_timeout(self, mock_run, mock_which):
        """Test ffmpeg subprocess timeout."""
        mock_which.return_value = None
        mock_run.side_effect = subprocess.TimeoutExpired(["ffmpeg", "-version"], 5)

        assert check_ffmpeg_installed() is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_ffmpeg_unexpected_exception(self, mock_run, mock_which):
        """Test unexpected exception during ffmpeg check."""
        mock_which.return_value = None
        mock_run.side_effect = Exception("Unexpected error")

        assert check_ffmpeg_installed() is False
