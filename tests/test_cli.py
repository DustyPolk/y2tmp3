"""Tests for CLI module."""

import tempfile
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from y2tmp3.cli import main


class TestCLI:
    """Test CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("y2tmp3.cli.download_youtube_as_mp3")
    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_output_directory")
    @patch("y2tmp3.cli.validate_youtube_url")
    def test_successful_download(
        self, mock_validate_url, mock_validate_dir, mock_check_ffmpeg, mock_download
    ):
        """Test successful download flow."""
        mock_validate_url.return_value = True
        mock_validate_dir.return_value = True
        mock_check_ffmpeg.return_value = True
        mock_download.return_value = "Test Video"

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "-o", tmpdir]
            )

        assert result.exit_code == 0
        assert "Successfully downloaded" in result.output
        mock_validate_url.assert_called_once()
        mock_check_ffmpeg.assert_called_once()
        mock_download.assert_called_once()

    @patch("y2tmp3.cli.validate_youtube_url")
    def test_invalid_url_exit(self, mock_validate_url):
        """Test exit on invalid URL."""
        mock_validate_url.return_value = False

        result = self.runner.invoke(main, ["invalid_url"])

        assert result.exit_code == 1
        assert "Invalid YouTube URL" in result.output

    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_youtube_url")
    def test_ffmpeg_not_installed_exit(self, mock_validate_url, mock_check_ffmpeg):
        """Test exit when ffmpeg not installed."""
        mock_validate_url.return_value = True
        mock_check_ffmpeg.return_value = False

        result = self.runner.invoke(main, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])

        assert result.exit_code == 1
        assert "ffmpeg is not installed" in result.output

    @patch("y2tmp3.cli.validate_output_directory")
    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_youtube_url")
    def test_invalid_output_directory_exit(
        self, mock_validate_url, mock_check_ffmpeg, mock_validate_dir
    ):
        """Test exit on invalid output directory."""
        mock_validate_url.return_value = True
        mock_check_ffmpeg.return_value = True
        mock_validate_dir.return_value = False

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "-o", tmpdir]
            )

        assert result.exit_code == 1
        assert "Invalid output directory" in result.output

    @patch("y2tmp3.cli.download_youtube_as_mp3")
    @patch("y2tmp3.cli.validate_output_directory")
    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_youtube_url")
    def test_download_exception_exit(
        self, mock_validate_url, mock_check_ffmpeg, mock_validate_dir, mock_download
    ):
        """Test exit on download exception."""
        mock_validate_url.return_value = True
        mock_check_ffmpeg.return_value = True
        mock_validate_dir.return_value = True
        mock_download.side_effect = Exception("Download failed")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(
                main, ["https://www.youtube.com/watch?v=dQw4w9WgXcQ", "-o", tmpdir]
            )

        assert result.exit_code == 1
        assert "Download failed" in result.output

    def test_list_formats(self):
        """Test format listing."""
        result = self.runner.invoke(main, ["--list-formats"])
        
        assert result.exit_code == 0
        assert "Supported Audio Formats" in result.output
        assert "mp3" in result.output
        assert "flac" in result.output

    def test_list_qualities(self):
        """Test quality listing."""
        result = self.runner.invoke(main, ["--list-qualities"])
        
        assert result.exit_code == 0
        assert "Supported Quality Levels" in result.output
        assert "192" in result.output
        assert "320" in result.output

    def test_help_output(self):
        """Test help output."""
        result = self.runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "Download YouTube videos as high-quality audio files" in result.output
        assert "--format" in result.output
        assert "--quality" in result.output
