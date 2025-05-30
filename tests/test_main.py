import sys
import pytest
import shutil
from unittest.mock import patch, MagicMock
from main import check_dependencies, main
from colorama import Fore

@pytest.fixture
def mock_shutil_which():
    with patch.object(shutil, 'which') as mock_which:
        yield mock_which

@pytest.fixture
def mock_exit():
    with patch.object(sys, 'exit') as mock_exit:
        yield mock_exit

@pytest.fixture
def mock_interface():
    with patch('main.Interface') as mock_interface_cls:
        instance = MagicMock()
        mock_interface_cls.return_value = instance
        yield instance

@pytest.fixture
def mock_manager():
    with patch('main.FeedManager') as mock_manager_cls:
        instance = MagicMock()
        mock_manager_cls.return_value = instance
        yield instance

def test_check_dependencies_missing_ffmpeg(mock_shutil_which, mock_exit):
    mock_shutil_which.side_effect = [None, '/usr/bin/mpv']
    check_dependencies()
    mock_exit.assert_called_once()

def test_check_dependencies_missing_mpv(mock_shutil_which, mock_exit):
    mock_shutil_which.side_effect = ['/usr/bin/ffmpeg', None]
    check_dependencies()
    mock_exit.assert_called_once()

def test_check_dependencies_all_present(mock_shutil_which, mock_exit):
    mock_shutil_which.side_effect = ['/usr/bin/ffmpeg', '/usr/bin/mpv']
    check_dependencies()
    mock_exit.assert_not_called()

def test_main_quit(mock_interface, mock_shutil_which):
    mock_shutil_which.side_effect = ['/usr/bin/ffmpeg', '/usr/bin/mpv']
    mock_interface.main_menu.side_effect = ['q']
    main()
    mock_interface.main_menu.assert_called_once()
    mock_interface.shut_down.assert_called_once()

def test_main_invalid_choice(mock_interface, mock_shutil_which):
    mock_shutil_which.side_effect = ['/usr/bin/ffmpeg', '/usr/bin/mpv']
    mock_interface.main_menu.side_effect = ['x', 'q']
    main()
    mock_interface.show_message.assert_called_with("Invalid choice!", "red")
    assert mock_interface.show_message.call_count == 1

def test_main_full_flow(mock_interface, mock_shutil_which):
    mock_shutil_which.side_effect = ['/usr/bin/ffmpeg', '/usr/bin/mpv']
    mock_interface.main_menu.side_effect = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'q']
    main()
    assert mock_interface.videos_menu.call_count == 1
    assert mock_interface.search_menu.call_count == 1
    assert mock_interface.watched_history.call_count == 1
    assert mock_interface.add_channel.call_count == 1
    assert mock_interface.list_channels.call_count == 1
    assert mock_interface.remove_channels.call_count == 1
    assert mock_interface.days_filter.call_count == 1
    assert mock_interface.length_filter.call_count == 1
    assert mock_interface.manage_api.call_count == 1
    assert mock_interface.shut_down.call_count == 1
