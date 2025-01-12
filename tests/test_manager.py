import json
import re
import pytest
from unittest.mock import patch, mock_open, MagicMock
import requests
from utils.manager import FeedManager
from utils.settings import MAX_SECONDS

@pytest.fixture
def manager():
    with patch('utils.manager.Extractor') as MockExtractor:
        instance = MockExtractor.return_value
        instance.get_channel_names.return_value = {'UC_x5XG1OV2P6uZZ5FSM9Ttw': 'Google Developers'}
        instance.load_cache.return_value = {}
        instance.save_cache.return_value = None
        m = FeedManager()
        m.channel_extractor = instance
        yield m

def test_load_config_file_exists(manager):
    mock_config = {"days_filter": 10, "api_key": "TEST_API_KEY", "min_video_length": 5}
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
    cleaned_text = FeedManager.remove_emojis(text)
    assert cleaned_text == "Hello world!"

def test_iso_duration_to_seconds_valid():
    duration = "PT1H30M15S"
    seconds = FeedManager.iso_duration_to_seconds(duration)
    assert seconds == 5415

def test_iso_duration_to_seconds_invalid(capfd):
    duration = "INVALID_DURATION"
    seconds = FeedManager.iso_duration_to_seconds(duration)
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
    clean_output = re.sub(r'\x1b\[[0-9;]*m', '', captured.out)
    assert "Timeout on first attempt" in clean_output
    assert "Timeout on second attempt" in clean_output
    assert mock_get.call_count == 2

def test_save_config(manager):
    manager.config = {"days_filter": 5, "api_key": "KEY", "min_video_length": 3}
    mocked_open_file = mock_open()
    with patch('os.makedirs'), patch('builtins.open', mocked_open_file):
        manager.save_config()
        mocked_open_file.assert_called_once_with('data/settings.json', 'w')
        handle = mocked_open_file()
        written_data = json.loads("".join(call_args[0][0] for call_args in handle.write.call_args_list))
        assert written_data['days_filter'] == 5
        assert written_data['api_key'] == "KEY"
        assert written_data['min_video_length'] == 3

def test_load_channels(manager):
    file_data = "UC12345\nUC67890"
    with patch('os.path.exists', return_value=True), patch('builtins.open', mock_open(read_data=file_data)):
        channels = manager.load_channels()
        assert channels == ["UC12345", "UC67890"]

def test_load_channels_not_exists(manager):
    with patch('os.path.exists', return_value=False):
        channels = manager.load_channels()
        assert channels == []

def test_save_channels(manager):
    manager.channels = ["UC111", "UC222"]
    mocked_open_file = mock_open()
    with patch('os.makedirs'), patch('builtins.open', mocked_open_file):
        manager.save_channels()
        mocked_open_file.assert_called_once_with('data/channels.yfe', 'w')
        handle = mocked_open_file()
        written_data = "".join(call_args[0][0] for call_args in handle.write.call_args_list)
        assert "UC111\nUC222" in written_data

def test_load_watched_not_exists(manager):
    with patch('os.path.exists', return_value=False):
        watched = manager.load_watched()
        assert watched == set()

def test_parse_feeds(manager):
    with patch.object(manager, 'parse_feed', return_value="feed_data") as mock_parse:
        result = manager.parse_feeds(["UC1", "UC2"])
        assert result == ["feed_data", "feed_data"]
        assert mock_parse.call_count == 2

def test_fetch_videos_no_entries(manager):
    feed = MagicMock(entries=[])
    with patch.object(manager.channel_extractor, 'load_cache', return_value={}):
        assert manager.fetch_videos("UC123", feed) == []

def test_fetch_videos_invalid_entry(manager):
    invalid_entry = MagicMock(id="invalid")
    feed = MagicMock(entries=[invalid_entry])
    with patch.object(manager.channel_extractor, 'load_cache', return_value={}):
        assert manager.fetch_videos("UC123", feed) == []

def test_fetch_videos_cached_valid(manager):
    entry_mock = MagicMock(
        id="yt:video:abc123",
        title="Test🚀Title",
        link="http://test",
        published="2020-01-01T00:00:00+00:00",
        author="Author",
        __contains__=MagicMock(return_value=True)
    )
    feed = MagicMock(entries=[entry_mock])
    cached_data = {
        "abc123": {
            'duration_seconds': 600,
            'live_broadcast_content': 'none',
            'published': "2020-01-01T00:00:00+00:00"
        }
    }
    with patch.object(manager.channel_extractor, 'load_cache', return_value=cached_data):
        videos = manager.fetch_videos("UC123", feed)
        assert len(videos) == 1
        assert videos[0]["id"] == "abc123"

def test_fetch_videos_cached_outside_range(manager):
    entry_mock = MagicMock(
        id="yt:video:abc123",
        title="TestTitle",
        link="http://test",
        published="2020-01-01T00:00:00+00:00",
        author="Author"
    )
    feed = MagicMock(entries=[entry_mock])
    cached_data = {
        "abc123": {
            'duration_seconds': MAX_SECONDS + 10,
            'live_broadcast_content': 'none',
            'published': "2020-01-01T00:00:00+00:00"
        }
    }
    with patch.object(manager.channel_extractor, 'load_cache', return_value=cached_data):
        assert manager.fetch_videos("UC123", feed) == []

def test_fetch_videos_uncached(manager):
    entry_mock = MagicMock(
        id="yt:video:abc123",
        title="Title",
        link="http://test",
        published="2020-01-01T00:00:00+00:00",
        author="Author",
        __contains__=MagicMock(return_value=True)
    )
    feed = MagicMock(entries=[entry_mock])

    with patch.object(manager.channel_extractor, 'load_cache', return_value={}), \
         patch.object(manager.channel_extractor.youtube.videos(), 'list', return_value=MagicMock(
             execute=MagicMock(return_value={
                 "items": [{
                     "id": "abc123",
                     "contentDetails": {"duration": "PT10M"}
                 }]
             })
         )):
        videos = manager.fetch_videos("UC123", feed)
        assert len(videos) == 1
        assert videos[0]["id"] == "abc123"
        assert videos[0]["title"] == "Title"
