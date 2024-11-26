from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class YouTubeChannelExtractor:
    def __init__(self, api_key: str):
        # Initialize YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_channel_id(self, link: str) -> str:
        # Get channel ID from YouTube URL
        if not link:
            raise ValueError("Link cannot be empty")
            
        link = link.strip()
        
        if "youtube.com/channel/" in link:
            channel_id = link.split("channel/")[-1].split("/")[0]
            if self._validate_channel_id(channel_id):
                return channel_id
                
        elif "/@" in link:
            username = link.split("/@")[-1].split("/")[0]
            return self._get_channel_id_from_username(username)
            
        elif "/user/" in link:
            username = link.split("/user/")[-1].split("/")[0]
            return self._get_channel_id_from_username(username)
            
        elif not any(x in link for x in ["youtube.com", "youtu.be"]):
            return self._get_channel_id_from_username(link)
            
        raise ValueError("Invalid channel link format")

    def _get_channel_id_from_username(self, username: str) -> str:
        # Get channel ID using YouTube Data API
        try:
            request = self.youtube.search().list(
                part="id",
                q=username,
                type="channel",
                maxResults=1
            )
            response = request.execute()
            
            if not response.get("items"):
                raise ValueError(f"No channel found for username: {username}")
                
            channel_id = response["items"][0]["id"]["channelId"]
            
            # Verify channel
            channel_response = self.youtube.channels().list(
                part="snippet",
                id=channel_id
            ).execute()
            
            if not channel_response.get("items"):
                raise ValueError(f"Could not verify channel for username: {username}")
                
            return channel_id
            
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
