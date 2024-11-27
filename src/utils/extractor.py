from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeChannelExtractor:
    def __init__(self, api_key: str):
        # Initialize YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.channel_name_cache = {}  # Cache to store channel names

    def get_channel_id(self, link: str) -> str:
        # Get channel ID from YouTube URL
        if not link:
            raise ValueError("Link cannot be empty")

        link = link.strip()

        if "youtube.com/channel/" in link:
            channel_id = link.split("channel/")[-1].split("/")[0]
            if self._validate_channel_id(channel_id):
                print(f'Your slug: {channel_id}')
                return channel_id
        elif "/@" in link or "/user/" in link:
            username = link.split("/")[-1]
            print(f'Your slug: {username}')
            return self._get_channel_id_from_username(username)
        elif not any(x in link for x in ["youtube.com", "youtu.be"]):
            print(f'Your slug: {link}')
            return self._get_channel_id_from_username(link)

        raise ValueError("Invalid channel link format")

    def _get_channel_id_from_username(self, username: str) -> str:
        # Get channel ID using YouTube Data API
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
        # Validate if channel ID exists
        try:
            response = self.youtube.channels().list(
                part="id",
                id=channel_id
            ).execute()
            return bool(response.get("items"))
        except HttpError:
            return False

    def get_channel_names(self, channel_ids: list[str]) -> dict:
        # Retrieve the names of YouTube channels
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

        return cached_names
