import pytest
from unittest.mock import patch, mock_open, MagicMock
import requests, json, re
from utils.manager import YouTubeFeedManager

@pytest.fixture
def manager():
    with patch('utils.manager.YouTubeChannelExtractor') as MockExtractor:
        instance = MockExtractor.return_value
        instance.get_channel_names.return_value = {'UC_x5XG1OV2P6uZZ5FSM9Ttw': 'Google Developers'}
        instance.load_cache.return_value = {}
        yield YouTubeFeedManager()

def test_load_config_file_exists(manager):
    mock_config = {
        "days_filter": 10,
        "api_key": "TEST_API_KEY",
        "min_video_length": 5
    }
    with patch('builtins.open', mock_open(read_data=json.dumps(mock_config))) as mocked_file:
        with patch('os.path.exists', return_value=True):
            config = manager.load_config()
            assert config['days_filter'] == 10
            assert config['api_key'] == "TEST_API_KEY"
            assert config['min_video_length'] == 5
            mocked_file.assert_called_once_with('data/settings.json', 'r')

def test_load_config_file_not_exists(manager):
    with patch('os.path.exists', return_value=False):
        config = manager.load_config()
        assert config == {"days_filter": 7, "api_key": "", "min_video_length": 2}

def test_remove_emojis():
    text = "Hello😊 World🚀!"
    cleaned_text = YouTubeFeedManager.remove_emojis(text)
    assert cleaned_text == "Hello world!"

def test_iso_duration_to_seconds_valid():
    duration = "PT1H30M15S"
    seconds = YouTubeFeedManager.iso_duration_to_seconds(duration)
    assert seconds == 5415

def test_iso_duration_to_seconds_invalid(capfd):
    duration = "INVALID_DURATION"
    seconds = YouTubeFeedManager.iso_duration_to_seconds(duration)
    captured = capfd.readouterr()
    assert seconds == 0
    assert "Invalid duration format" in captured.out

@patch('utils.manager.requests.get')
def test_parse_feed_success(mock_get, manager):
    mock_response = MagicMock()
    mock_response.content = '<rss><channel><item><id>video1</id></item></channel></rss>'
    mock_get.return_value = mock_response
    feed = manager.parse_feed('UCjay7c-KSW2nC8Grq_q8tHg')
    assert feed is not None
    mock_get.assert_called_once()

@patch('utils.manager.requests.get', side_effect=requests.exceptions.Timeout)
def test_parse_feed_timeout(mock_get, manager, capfd):
    feed = manager.parse_feed('UCjay7c-KSW2nC8Grq_q8tHg')
    assert feed is None
    captured = capfd.readouterr()
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    clean_output = ansi_escape.sub('', captured.out)
    assert "Timeout on first attempt" in clean_output
    assert "Timeout on second attempt" in clean_output
    assert mock_get.call_count == 2
