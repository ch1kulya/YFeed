import sys
import pytest
import shutil
from unittest.mock import patch, MagicMock
from main import check_dependencies, main

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
    with patch('main.YouTubeFeedManager') as mock_manager_cls:
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
