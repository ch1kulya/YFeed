import os
import json
import re
import shutil
import subprocess
import feedparser
import requests
import concurrent.futures
from colorama import Fore, Style
from datetime import datetime
from typing import Dict, List, Set
from googleapiclient.errors import HttpError
from utils.settings import CONFIG_FILE, CHANNELS_FILE, WATCHED_FILE, MAX_SECONDS, CACHE_FILE, TIMEOUT_SECONDS
from utils.extractor import YouTubeChannelExtractor

class YouTubeFeedManager:
    """Manages YouTube feed operations, including loading configurations, channels,
    watched videos, and fetching video data from YouTube channels."""

    def __init__(self):
        """Initialize the YouTubeFeedManager instance.

        This method loads the configuration, channels, and watched videos from their
        respective files. It also initializes the YouTubeChannelExtractor if an API key
        is provided in the configuration.
        """
        # Initialize the feed manager
        self.config = self.load_config()
        self.channels = self.load_channels()
        self.watched = self.load_watched()
        self.channel_extractor = None
        
        # Initialize API if key exists
        if self.config.get('api_key'):
            self.channel_extractor = YouTubeChannelExtractor(self.config['api_key'])

    @staticmethod
    def load_config() -> Dict:
        """Load configuration settings from a JSON file.

        If the configuration file does not exist, it returns default settings.

        Returns:
            Dict: A dictionary containing configuration settings.
        """
        default_config = {"days_filter": 7, "api_key": "", "min_video_length": 2}
        if not os.path.exists(CONFIG_FILE):
            return default_config
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return {**default_config, **config}

    def save_config(self) -> None:
        """Save the current configuration settings to a JSON file.

        Creates the necessary directories if they do not exist.
        """
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    @staticmethod
    def load_channels() -> List[str]:
        """Load the list of subscribed YouTube channel IDs from a file.

        If the channels file does not exist, it returns an empty list.

        Returns:
            List[str]: A list of YouTube channel IDs.
        """
        if not os.path.exists(CHANNELS_FILE):
            return []
        with open(CHANNELS_FILE, "r") as f:
            return [line.strip() for line in f]

    def save_channels(self) -> None:
        """Save the current list of subscribed YouTube channel IDs to a file.

        Creates the necessary directories if they do not exist.
        """
        os.makedirs(os.path.dirname(CHANNELS_FILE), exist_ok=True)
        with open(CHANNELS_FILE, "w") as f:
            f.write("\n".join(self.channels))

    @staticmethod
    def load_watched() -> Set[str]:
        """Load the set of watched video IDs from a file.

        If the watched file does not exist, it returns an empty set.

        Returns:
            Set[str]: A set of watched video IDs.
        """
        if not os.path.exists(WATCHED_FILE):
            return set()
        with open(WATCHED_FILE, "r") as f:
            return set(line.strip() for line in f)

    def save_watched(self) -> None:
        """Save the current set of watched video IDs to a file.

        Creates the necessary directories if they do not exist.
        """
        os.makedirs(os.path.dirname(WATCHED_FILE), exist_ok=True)
        with open(WATCHED_FILE, "w") as f:
            f.write("\n".join(self.watched))
            
    @staticmethod
    def remove_emojis(text: str) -> str:
        """Remove emojis and special characters from the given text.

        Converts the text to lowercase and capitalizes it after removing emojis.

        Args:
            text (str): The text from which to remove emojis.

        Returns:
            str: The cleaned text without emojis.
        """
        emoji_pattern = re.compile(
            "["
            "\U0001F300-\U0001FAFF"
            "\U000024C2-\U000027B0"
            "]+",
            flags=re.UNICODE
        )
        normal_text = emoji_pattern.sub(r'', text).lower().capitalize()
        return normal_text
    
    @staticmethod
    def iso_duration_to_seconds(duration: str) -> int:
        """Convert an ISO 8601 duration string to total seconds.

        Args:
            duration (str): The duration string in ISO 8601 format (e.g., 'PT1H30M15S').

        Returns:
            int: The total duration in seconds.

        If the duration format is invalid, it prints an error message and returns 0.
        """
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?|P(\d+)D?", duration)
        if not match:
            print(f"Invalid duration format: {duration}")
            return 0
        days = int(match.group(4)) if match.group(4) else 0
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        return days * 86400 + hours * 3600 + minutes * 60 + seconds
    
    def parse_feed(self, channel_id):
        """Fetch and parse the YouTube feed for a given channel ID with retries.

        Args:
            channel_id (str): The YouTube channel ID to fetch the feed for.

        Returns:
            feedparser.FeedParserDict or None: The parsed feed data, or None if fetching failed after retries.
        """
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=TIMEOUT_SECONDS)
                feed = feedparser.parse(response.content)
                return feed
            except requests.exceptions.Timeout:
                if attempt == 0:
                    print(f"{Fore.RED}Timeout{Fore.WHITE} on first attempt for channel {self.channel_extractor.get_channel_names([channel_id]).get(channel_id, "Unknown")}.{Style.RESET_ALL} Retrying...")
                else:
                    print(f"{Fore.RED}Timeout{Fore.WHITE} on second attempt for channel {self.channel_extractor.get_channel_names([channel_id]).get(channel_id, "Unknown")}.{Style.RESET_ALL} Giving up.")
                if attempt == 1:
                    return None
            except Exception as e:
                print(f"{Fore.RED}Error parsing {channel_id}: {Fore.WHITE}{e}{Style.RESET_ALL}")
                return None

    def parse_feeds(self, channel_ids):
        """Fetch and parse YouTube feeds concurrently for a list of channel IDs.

        Args:
            channel_ids (list): A list of YouTube channel IDs.

        Returns:
            list: A list of parsed feed data for each channel ID.
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(self.parse_feed, channel_ids))
        return results

    def fetch_videos(self, channel_id: str, feed) -> List[Dict]:
        """Fetch videos from a YouTube channel feed, applying filters and caching.

        Args:
            channel_id (str): The ID of the YouTube channel.
            feed: The parsed feed data from the channel's RSS feed.

        Returns:
            List[Dict]: A list of video information dictionaries that meet the criteria.

        This method loads existing cache data, checks for new videos, filters them based
        on duration and live status, updates the cache, and returns the list of videos.
        """
        try:
            # Load existing cache
            video_cache = self.channel_extractor.load_cache(CACHE_FILE)

            if not feed.entries:
                print(Fore.RED + "No entries found in the feed.")
                return []

            # Collect video IDs to fetch details for
            video_ids_to_fetch = []
            cached_videos = []
            need_api_request = False

            for entry in feed.entries:
                if "id" not in entry or ":" not in entry.id:
                    print(Fore.YELLOW + f"Skipping invalid entry: {entry}")
                    continue

                video_id = entry.id.split(":")[-1]
                
                # Check if video details are already in cache
                if video_id in video_cache:
                    cached_video = video_cache[video_id]
                    
                    # Validate cached video meets current criteria
                    total_seconds = cached_video.get('duration_seconds', 0)
                    published_date = cached_video.get('published')

                    if (self.config.get("min_video_length", 2) * 60 <= total_seconds <= MAX_SECONDS and 
                        cached_video.get('live_broadcast_content') not in ["live", "upcoming"]):
                        
                        try:
                            # Convert string to datetime if needed
                            if isinstance(published_date, str):
                                published_date = datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S%z")
                            
                            cached_videos.append({
                                "title": self.remove_emojis(entry.title),
                                "link": entry.link,
                                "published": published_date,
                                "id": video_id,
                                "author": entry.author if 'author' in entry else "Unknown",
                            })
                        except ValueError:
                            print(f"Invalid date format for cached entry: {published_date}")
                            video_ids_to_fetch.append(video_id)
                else:
                    video_ids_to_fetch.append(video_id)
                    need_api_request = True

            if not need_api_request:
                return cached_videos

            # Fetch details for uncached videos
            if video_ids_to_fetch:
                try:
                    video_response = self.channel_extractor.youtube.videos().list(
                        part="contentDetails",
                        id=','.join(video_ids_to_fetch)
                    ).execute()

                    if "items" not in video_response or not video_response["items"]:
                        print(Fore.RED + "No video details found in the API response.")
                        return cached_videos

                    # Process new videos and update cache
                    for entry in feed.entries:
                        video_id = entry.id.split(":")[-1]
                        if video_id not in video_ids_to_fetch:
                            continue

                        items = [item for item in video_response.get("items", []) if item["id"] == video_id]
                        if not items:
                            continue
                        
                        item = items[0]
                        duration = item["contentDetails"]["duration"]
                        total_seconds = self.iso_duration_to_seconds(duration)
                        live_broadcast_content = item.get("liveBroadcastContent")
                        
                        # Cache the video details
                        cache_data = self.channel_extractor.load_cache(CACHE_FILE)
                        if video_id not in cache_data:
                            video_cache[video_id] = {
                                'duration_seconds': total_seconds,
                                'live_broadcast_content': live_broadcast_content,
                                'published': entry.published
                            }
                        self.channel_extractor.save_cache(cache_data, CACHE_FILE)                        
                    
                        if live_broadcast_content in ["live", "upcoming"]:
                            continue  # Skip streams and upcoming broadcasts

                        if total_seconds < self.config.get("min_video_length", 2) * 60 or total_seconds > MAX_SECONDS:
                            continue
                        
                        try:
                            published_date = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            print(f"Invalid date format for entry: {entry.published}")
                            continue

                        # Add to videos list
                        cached_videos.append({
                            "title": self.remove_emojis(entry.title),
                            "link": entry.link,
                            "published": published_date,
                            "id": video_id,
                            "author": entry.author if 'author' in entry else "Unknown",
                        })

                    # Save updated cache
                    self.channel_extractor.save_cache(video_cache, CACHE_FILE)

                    return cached_videos

                except HttpError as e:
                    print(Fore.RED + f"Error fetching video details: {e}")
                    return cached_videos

            return cached_videos

        except Exception as e:
            print(Fore.RED + f"Error fetching videos for channel {channel_id}: {str(e)}")
            return []

    def search_youtube_videos(self, search_query: str) -> List[Dict]:
        """
        Search YouTube for videos matching the query and return the top 8 videos with their details.

        Args:
            search_query (str): The search term to query YouTube.

        Returns:
            List[Dict]: A list of dictionaries containing video title, description, and duration.
        """
        try:
            search_response = self.channel_extractor.youtube.search().list(
                q=search_query,
                part='id,snippet',
                type='video',
                maxResults=8
            ).execute()
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            if not video_ids:
                print(Fore.YELLOW + "No videos found for the given search query.")
                return []
            videos_response = self.channel_extractor.youtube.videos().list(
                part='snippet,contentDetails',
                id=','.join(video_ids)
            ).execute()
            videos = []
            for item in videos_response.get('items', []):
                title = item['snippet']['title']
                channel_title = item['snippet']['channelTitle']
                iso_duration = item['contentDetails']['duration']
                duration = self.iso_duration_to_seconds(iso_duration)
                live_broadcast_content = item['snippet'].get('liveBroadcastContent')
                if live_broadcast_content in ["live", "upcoming"]:
                    continue
                if (duration < self.config.get("min_video_length", 2) * 60) or (duration > MAX_SECONDS):
                    continue
                videos.append({
                    "id": item['id'],
                    "title": self.remove_emojis(title),
                    "duration": duration,
                    "author": channel_title
                })
            return videos
        except HttpError as e:
            print(Fore.RED + f"An HTTP error occurred: {e}")
            return []
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
            return []

    def open_video_instance(self, link: str) -> None:
        if os.name == "nt":  # Windows
            if shutil.which("wt.exe"):
                subprocess.Popen(f'wt.exe -w 0 new-tab -- python src/instance.py "{link}"', shell=True)
            else:
                subprocess.Popen(f'start cmd /C python src/instance.py "{link}"', shell=True)
        # TODO: Linux/Mac support
