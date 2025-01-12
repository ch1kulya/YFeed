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
    watch_video("https://www.youtube.com/watch?v=test")
    mock_mediaplayer.watch_video.assert_called_once_with("https://www.youtube.com/watch?v=test")

def test_main_no_args(mock_exit, capsys):
    with patch.object(sys, 'argv', ['instance.py']):
        with pytest.raises(SystemExit):
            main()
    mock_exit.assert_called_once()
    captured = capsys.readouterr()
    assert "No video link." in captured.out

def test_main_with_args(mock_mediaplayer):
    with patch.object(sys, 'argv', ['instance.py', 'https://www.youtube.com/watch?v=test']):
        main()
    mock_mediaplayer.watch_video.assert_called_once_with("https://www.youtube.com/watch?v=test")

def test_main_with_multiple_args(mock_mediaplayer):
     with patch.object(sys, 'argv', ['instance.py', 'https://www.youtube.com/watch?v=test', 'extra', 'args']):
        main()
     mock_mediaplayer.watch_video.assert_called_once_with("https://www.youtube.com/watch?v=test")
