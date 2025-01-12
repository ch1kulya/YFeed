import pytest
import sys
from unittest.mock import patch, MagicMock
from instance import main, watch_video

@pytest.fixture
def mock_mediaplayer():
    with patch('instance.MediaPlayer') as mock_player_cls:
        instance = MagicMock()
        mock_player_cls.return_value = instance
        yield instance

@pytest.fixture
def mock_exit():
    with patch.object(sys, 'exit', side_effect=SystemExit) as mock_exit:
        yield mock_exit

def test_watch_video(mock_mediaplayer):
    watch_video("http://example.com/video")
    mock_mediaplayer.watch_video.assert_called_once_with("http://example.com/video")

def test_main_no_args(mock_exit):
    with patch.object(sys, 'argv', ['instance.py']):
        with pytest.raises(SystemExit):
            main()
    mock_exit.assert_called_once()

def test_main_with_args(mock_mediaplayer):
    with patch.object(sys, 'argv', ['instance.py', 'http://example.com/video']):
        main()
    mock_mediaplayer.watch_video.assert_called_once_with("http://example.com/video")
