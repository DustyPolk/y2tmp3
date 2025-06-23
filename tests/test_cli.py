"""Tests for CLI module."""

from unittest.mock import patch

import pytest

from y2tmp3.cli import main


class TestCLI:
    """Test CLI functionality."""

    @patch("y2tmp3.cli.download_youtube_as_mp3")
    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_output_directory")
    @patch("y2tmp3.cli.validate_youtube_url")
    @patch("sys.argv", ["y2tmp3", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    def test_successful_download(
        self, mock_validate_url, mock_validate_dir, mock_check_ffmpeg, mock_download
    ):
        """Test successful download flow."""
        mock_validate_url.return_value = True
        mock_validate_dir.return_value = True
        mock_check_ffmpeg.return_value = True
        mock_download.return_value = "Test Video"

        # Should not raise SystemExit
        main()

        mock_validate_url.assert_called_once()
        mock_validate_dir.assert_called_once()
        mock_check_ffmpeg.assert_called_once()
        mock_download.assert_called_once()

    @patch("y2tmp3.cli.validate_youtube_url")
    @patch("sys.argv", ["y2tmp3", "invalid_url"])
    def test_invalid_url_exit(self, mock_validate_url):
        """Test exit on invalid URL."""
        mock_validate_url.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_youtube_url")
    @patch("sys.argv", ["y2tmp3", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    def test_ffmpeg_not_installed_exit(self, mock_validate_url, mock_check_ffmpeg):
        """Test exit when ffmpeg not installed."""
        mock_validate_url.return_value = True
        mock_check_ffmpeg.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("y2tmp3.cli.validate_output_directory")
    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_youtube_url")
    @patch(
        "sys.argv",
        ["y2tmp3", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "-o", "/invalid/dir"],
    )
    def test_invalid_output_directory_exit(
        self, mock_validate_url, mock_check_ffmpeg, mock_validate_dir
    ):
        """Test exit on invalid output directory."""
        mock_validate_url.return_value = True
        mock_check_ffmpeg.return_value = True
        mock_validate_dir.return_value = False

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("y2tmp3.cli.download_youtube_as_mp3")
    @patch("y2tmp3.cli.validate_output_directory")
    @patch("y2tmp3.cli.check_ffmpeg_installed")
    @patch("y2tmp3.cli.validate_youtube_url")
    @patch("sys.argv", ["y2tmp3", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    def test_download_exception_exit(
        self, mock_validate_url, mock_check_ffmpeg, mock_validate_dir, mock_download
    ):
        """Test exit on download exception."""
        mock_validate_url.return_value = True
        mock_check_ffmpeg.return_value = True
        mock_validate_dir.return_value = True
        mock_download.side_effect = Exception("Download failed")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
