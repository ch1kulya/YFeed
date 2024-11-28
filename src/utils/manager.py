import os
import json
import feedparser
import re
from time import time
from colorama import Fore, Style, Cursor
from datetime import datetime
from typing import Dict, List, Set
from googleapiclient.errors import HttpError
from utils.settings import CONFIG_FILE, CHANNELS_FILE, WATCHED_FILE, MAX_SECONDS, CACHE_FILE
from utils.extractor import YouTubeChannelExtractor
import asyncio
import aiohttp
from aiohttp import ClientError

class YouTubeFeedManager:
    def __init__(self):
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
        # Load configuration from file
        default_config = {"days_filter": 7, "api_key": "", "min_video_length": 2}
        if not os.path.exists(CONFIG_FILE):
            return default_config
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return {**default_config, **config}

    def save_config(self) -> None:
        # Save configuration to file
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)
            
    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as cache_file:
                return json.load(cache_file)
        return {}

    def save_cache(self, cache_data):
        with open(CACHE_FILE, "w") as cache_file:
            json.dump(cache_data, cache_file)

    @staticmethod
    def load_channels() -> List[str]:
        # Load channel list from file
        if not os.path.exists(CHANNELS_FILE):
            return []
        with open(CHANNELS_FILE, "r") as f:
            return [line.strip() for line in f]

    def save_channels(self) -> None:
        # Save channel list to file
        os.makedirs(os.path.dirname(CHANNELS_FILE), exist_ok=True)
        with open(CHANNELS_FILE, "w") as f:
            f.write("\n".join(self.channels))

    @staticmethod
    def load_watched() -> Set[str]:
        # Load history from file
        if not os.path.exists(WATCHED_FILE):
            return set()
        with open(WATCHED_FILE, "r") as f:
            return set(line.strip() for line in f)

    def save_watched(self) -> None:
        # Save history to file
        os.makedirs(os.path.dirname(WATCHED_FILE), exist_ok=True)
        with open(WATCHED_FILE, "w") as f:
            f.write("\n".join(self.watched))
            
    @staticmethod
    def remove_emojis(text: str) -> str:
        # Remove emojis from text
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"  # Dingbats
            "\U000024C2-\U0001F251"  # Enclosed characters
            "]+",
            flags=re.UNICODE
        )
        normal_text = emoji_pattern.sub(r'', text).lower().capitalize()
        return normal_text
    
    @staticmethod
    def iso_duration_to_seconds(duration: str) -> int:
        # Convert ISO 8601 duration format to total seconds
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?|P(\d+)D?", duration)
        if not match:
            print(f"Invalid duration format: {duration}")
            return 0
        days = int(match.group(4)) if match.group(4) else 0
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        return days * 86400 + hours * 3600 + minutes * 60 + seconds
    
    async def fetch_feed(self, url: str) -> dict:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.read()
                    return feedparser.parse(data)
            except ClientError as e:
                print(Fore.RED + f"HTTP error during feed fetch: {e}")
                return feedparser.parse('')
            except asyncio.TimeoutError:
                print(Fore.RED + "Feed fetch timed out.")
                return feedparser.parse('')

    def fetch_videos(self, channel_id: str) -> List[Dict]:
        try:
            # Load existing cache
            video_cache = self.load_cache()

            # Fetch the feed data from the channel
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed_start_time = time()
            feed = asyncio.run(self.fetch_feed(url))
            feed_time = (time() - feed_start_time) * 1000
            print(f"Feed fetching time: {Fore.LIGHTRED_EX if feed_time > 750 else Fore.LIGHTGREEN_EX}{int(feed_time)}{Style.RESET_ALL} ms")

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
                print(Fore.GREEN + f"Videos from {channel_id} fetched!")
                return cached_videos

            # Fetch details for uncached videos
            if video_ids_to_fetch:
                try:
                    api_start_time = time()
                    video_response = self.channel_extractor.youtube.videos().list(
                        part="contentDetails",
                        id=','.join(video_ids_to_fetch)
                    ).execute()
                    api_time = (time() - api_start_time) * 1000
                    print(f"API request time: {Fore.LIGHTRED_EX if api_time > 500 else Fore.LIGHTGREEN_EX}{int(api_time)}{Style.RESET_ALL} ms")
                    print(f"API requests made: {Fore.LIGHTYELLOW_EX}{len(video_ids_to_fetch)}{Style.RESET_ALL}")

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
                        cache_data = self.load_cache()
                        if video_id not in cache_data:
                            video_cache[video_id] = {
                                'duration_seconds': total_seconds,
                                'live_broadcast_content': live_broadcast_content,
                                'published': entry.published
                            }
                        self.save_cache(cache_data)                        
                    
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
                    self.save_cache(video_cache)
                    print(Fore.GREEN + f"Videos from {channel_id} fetched!")

                    return cached_videos

                except HttpError as e:
                    print(Fore.RED + f"Error fetching video details: {e}")
                    return cached_videos

            return cached_videos

        except Exception as e:
            print(Fore.RED + f"Error fetching videos for channel {channel_id}: {str(e)}")
            return []
