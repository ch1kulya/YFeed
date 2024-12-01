import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.settings import NAMES_FILE

class YouTubeChannelExtractor:
    """Extracts YouTube channel information using the YouTube Data API.

    This class provides methods to retrieve channel IDs from YouTube URLs,
    validate channel IDs, and fetch channel names. It also handles caching
    of channel names to reduce API calls.
    """

    def __init__(self, api_key: str):
        """Initialize the YouTubeChannelExtractor with a YouTube Data API key.

        Args:
            api_key (str): The YouTube Data API key for making API requests.
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.channel_name_cache = self.load_cache(NAMES_FILE)  # Cache to store channel names
        
    def load_cache(self, file):
        """Load cached data from a JSON file.

        Args:
            file (str): The path to the cache file.

        Returns:
            dict: A dictionary containing the cached data. Returns an empty dictionary if the file doesn't exist.
        """
        if os.path.exists(file):
            with open(file, "r") as cache_file:
                return json.load(cache_file)
        return {}

    def save_cache(self, cache_data, file):
        """Save data to a cache file in JSON format.

        Args:
            cache_data (dict): The data to be cached.
            file (str): The path to the cache file.
        """
        with open(file, "w") as cache_file:
            json.dump(cache_data, cache_file)

    def get_channel_id(self, link: str) -> str:
        """Extract the YouTube channel ID from a given URL or username.

        Args:
            link (str): The YouTube channel URL or username.

        Returns:
            str: The extracted channel ID.

        Raises:
            ValueError: If the link is empty or in an invalid format.
        """
        if not link:
            raise ValueError("Link cannot be empty")

        link = link.strip()

        if "youtube.com/channel/" in link:
            channel_id = link.split("channel/")[-1].split("/")[0]
            if self._validate_channel_id(channel_id):
                return channel_id
        elif "/@" in link or "/user/" in link:
            username = link.split("/")[-1]
            return self._get_channel_id_from_username(username)
        elif not any(x in link for x in ["youtube.com", "youtu.be"]):
            return self._get_channel_id_from_username(link)

        raise ValueError("Invalid channel link format")

    def _get_channel_id_from_username(self, username: str) -> str:
        """Retrieve the channel ID using a username via the YouTube Data API.

        Args:
            username (str): The username or custom URL of the YouTube channel.

        Returns:
            str: The channel ID corresponding to the given username.

        Raises:
            ValueError: If no channel is found, the channel has fewer than 100 subscribers, or an API error occurs.
        """
        try:
            request = self.youtube.search().list(
                part="id",
                q=username,
                type="channel",
                maxResults=3
            )
            response = request.execute()

            if not response.get("items"):
                raise ValueError(f"No channel found for username: {username}")
            
            channels = []
            for item in response["items"]:
                channel_id = item["id"]["channelId"]
                channel_request = self.youtube.channels().list(
                    part="statistics",
                    id=channel_id
                )
                channel_response = channel_request.execute()
                subscribers_count = int(channel_response["items"][0]["statistics"]["subscriberCount"])
                channels.append((channel_id, subscribers_count))
            
            best_channel = max(channels, key=lambda x: x[1])
            if best_channel[1] < 100:
                raise ValueError(f"Channel does not have at least 100 subscribers")
            return best_channel[0]
        except HttpError as e:
            raise ValueError(f"YouTube API error: {str(e)}")

    def _validate_channel_id(self, channel_id: str) -> bool:
        """Validate whether a channel ID exists on YouTube.

        Args:
            channel_id (str): The channel ID to validate.

        Returns:
            bool: True if the channel ID exists, False otherwise.
        """
        try:
            response = self.youtube.channels().list(
                part="id",
                id=channel_id
            ).execute()
            return bool(response.get("items"))
        except HttpError:
            return False

    def get_channel_names(self, channel_ids: list[str]) -> dict:
        """Retrieve the names of YouTube channels given their IDs.

        Args:
            channel_ids (list[str]): A list of YouTube channel IDs.

        Returns:
            dict: A dictionary mapping channel IDs to their names.

        This method uses a cache to avoid unnecessary API calls. It updates the cache with any new channel names retrieved.
        """
        cached_names = {cid: name for cid, name in self.channel_name_cache.items() if cid in channel_ids}
        remaining_ids = [cid for cid in channel_ids if cid not in cached_names]

        if not remaining_ids:
            return cached_names

        try:
            # Perform batch request to retrieve channel details
            request = self.youtube.channels().list(
                part="snippet",
                id=",".join(remaining_ids)
            )
            response = request.execute()

            # Map channel IDs to names and cache them
            for item in response.get("items", []):
                channel_id = item["id"]
                channel_name = item["snippet"]["title"]
                self.channel_name_cache[channel_id] = channel_name
                cached_names[channel_id] = channel_name

            for channel_id in remaining_ids:
                if channel_id not in cached_names:
                    cached_names[channel_id] = "Unknown"
                    self.channel_name_cache[channel_id] = "Unknown"

        except HttpError as e:
            print(f"YouTube API error: {str(e)}")
            for channel_id in remaining_ids:
                cached_names[channel_id] = "Unknown"
                self.channel_name_cache[channel_id] = "Unknown"
                
        self.save_cache(self.channel_name_cache, NAMES_FILE)

        return cached_names
