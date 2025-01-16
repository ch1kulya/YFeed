import os
import json
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.settings import NAMES_FILE

class Extractor:
    """Extracts YouTube channel information using the YouTube Data API.

    This class provides methods to retrieve channel IDs from YouTube URLs,
    validate channel IDs, and fetch channel names. It also handles caching
    of channel names to reduce API calls.
    """

    def __init__(self, api_key: str):
        """Initialize the Extractor with a YouTube Data API key.

        Args:
            api_key (str): The YouTube Data API key for making API requests.
        """
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.channel_name_cache = self.load_cache(NAMES_FILE)
        
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
        """Extract the YouTube channel ID or handle from a given URL.

        Args:
            link (str): The YouTube channel URL.

        Returns:
            str: The extracted channel ID or handle.

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
        elif "/@" in link:
            handle = link.split("/@")[-1].split("/")[0]
            return self.get_channel_id_from_handle(handle)
        elif link.startswith("@"):
            handle = link[1:].split("/")[0]
            return self.get_channel_id_from_handle(handle)

        raise ValueError("Invalid channel link format")

    def get_channel_id_from_handle(self, handle: str) -> str:
        """Retrieve the channel ID using a handle via the YouTube Data API.

        Args:
            handle (str): The handle of the YouTube channel.

        Returns:
            str: The channel ID corresponding to the given handle.

        Raises:
            ValueError: If no channel is found or an API error occurs.
        """
        try:
            request = self.youtube.channels().list(
                part="id",
                forHandle=handle
            )
            response = request.execute()

            if not response.get("items"):
                raise ValueError(f"No channel found for handle: {handle}")
            
            channel_id = response["items"][0]["id"]
            return channel_id
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
        cached_names = {cid: self.channel_name_cache[cid] for cid in channel_ids if cid in self.channel_name_cache}
        remaining_ids = [cid for cid in channel_ids if cid not in cached_names]
        if not remaining_ids:
            return cached_names

        try:
            response = self.youtube.channels().list(
                part="snippet",
                id=",".join(remaining_ids)
            ).execute()

            new_names = {item["id"]: item["snippet"]["title"] for item in response.get("items", [])}
            self.channel_name_cache.update(new_names)
            cached_names.update(new_names)

        except HttpError as e:
            raise ValueError(f"YouTube API error: {str(e)}")

        for cid in remaining_ids:
            cached_names.setdefault(cid, "Unknown")
            self.channel_name_cache.setdefault(cid, "Unknown")

        self.save_cache(self.channel_name_cache, NAMES_FILE)
        return cached_names
    
    def get_channel_info(self, channel_id: str) -> dict:
        """Retrieve detailed information about a YouTube channel by its ID.

        Args:
            channel_id (str): The ID of the YouTube channel.

        Returns:
            dict: A dictionary containing the channel's title, description,
                  subscriber count, total video count, and URL. Returns None if an error occurs or data isn't found.
        """
        try:
            response = self.youtube.channels().list(
                part="snippet,statistics",
                id=channel_id
            ).execute()

            if not response.get("items"):
                return None

            item = response["items"][0]
            snippet = item["snippet"]
            statistics = item["statistics"]
            
            channel_info = {
                "title": snippet.get("title", "Unknown"),
                "description": re.sub(r'\s+', ' ', snippet.get("description", "No description")).strip(),
                "subscribers": statistics.get("subscriberCount", "Unknown"),
                "total_videos": statistics.get("videoCount", "Unknown"),
                "url": f"https://www.youtube.com/channel/{channel_id}"
            }
            return channel_info

        except HttpError as e:
            raise ValueError(f"YouTube API error: {str(e)}")
