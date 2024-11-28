import os
import sys
import json
import feedparser
import webbrowser
import re
from time import sleep, time
from colorama import Fore, Style, Cursor
from datetime import datetime
from typing import Dict, List, Set
from googleapiclient.errors import HttpError
from yt_dlp import YoutubeDL
import vlc
from tqdm import tqdm
from utils.settings import CONFIG_FILE, CHANNELS_FILE, WATCHED_FILE, MAX_SECONDS, CACHE_FILE
from utils.extractor import YouTubeChannelExtractor
import asyncio
import aiohttp
from aiohttp import ClientError

class QuietLogger:
    def debug(self, msg):
        pass
    def info(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

class YouTubeFeedManager:
    def __init__(self):
        # Initialize the feed manager
        self.config = self.load_config()
        self.channels = self.load_channels()
        self.watched = self.load_watched()
        self.channel_extractor = None
        self.progress_bar = None
        
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

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', d.get('total_bytes_estimate', 0))
            downloaded_bytes = d.get('downloaded_bytes', 0)

            if self.progress_bar is None and total_bytes > 0:
                self.progress_bar = tqdm(total=total_bytes, unit='B', unit_scale=True, desc="Downloading", dynamic_ncols=True)

            if self.progress_bar is not None:
                self.progress_bar.update(downloaded_bytes - self.progress_bar.n)

        elif d['status'] == 'finished':
            if self.progress_bar is not None:
                self.progress_bar.close()
                self.progress_bar = None
    
    def watch_video(self, url):
        temp_file = "temp"  # Temporary file to hold the video

        # yt-dlp options for downloading the best video+audio quality
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',  # Set quality
            'outtmpl': temp_file,                 # Save video temporarily
            'progress_hooks': [self.download_progress_hook],  # Add progress hook
            'quiet': True,                        # Suppress logs for cleaner output
            'no_warnings': True,
            'logger': QuietLogger(),
            'max-downloads': 8,
            'concurrent_fragments': 8,
            'nooverwrites': False,
        }

        try:
            # Clean up temporary file
            if os.path.exists(temp_file + ".webm"):
                os.remove(temp_file + ".webm")
                print(Style.DIM + "Temporary file removed.")
            # Download the video
            with YoutubeDL(ydl_opts) as ydl:
                print(Style.DIM + "Downloading video...")
                ydl.download([url])
            
            # Play the video using python-vlc
            print(Style.DIM + "Playing video...")
            self.play_video(temp_file + ".webm")
            
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
            print(Style.DIM + "Playing in browser.")
            sleep(5)
            webbrowser.open(url)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file + ".webm"):
                os.remove(temp_file + ".webm")
                print(Style.DIM + "Temporary file removed.")
                
    def play_video(self, video_file):
        # Create a VLC instance
        instance = vlc.Instance('--no-video-title-show', '--quiet', '--intf=dummy')
        player = instance.media_player_new()

        # Load the video file into VLC player
        media = instance.media_new(video_file)
        player.set_media(media)
        player.set_fullscreen(False)
        player.audio_set_volume(50)

        # Play the video
        player.play()

        print(f"\n{Style.BRIGHT}Video Controls{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1.{Fore.WHITE} '{Fore.YELLOW}go{Fore.WHITE} [{Fore.YELLOW}percentage{Fore.WHITE}]'{Fore.LIGHTBLACK_EX} — Move to the given percentage of the video")
        print(f"{Fore.CYAN}2.{Fore.WHITE} '{Fore.YELLOW}v{Fore.WHITE} [{Fore.YELLOW}volume{Fore.WHITE}]'{Fore.LIGHTBLACK_EX} — Set volume (1 to 100)")
        print(f"{Fore.CYAN}3.{Fore.WHITE} '{Fore.YELLOW}p{Fore.WHITE}'{Fore.LIGHTBLACK_EX} — Pause or resume the video")
        print(f"{Fore.CYAN}4.{Fore.WHITE} '{Fore.YELLOW}q{Fore.WHITE}'{Fore.LIGHTBLACK_EX} — Quit the player{Style.RESET_ALL}")
        
        # Output placeholders
        output_row = 24
        input_row = 23
        def clear_line(row):
            sys.stdout.write(f"{Cursor.POS(1, row)}{' ' * os.get_terminal_size().columns}{Cursor.POS(1, row)}")
            sys.stdout.flush()
        
        while True:
            clear_line(input_row)
            # Wait for user input for controls
            sys.stdout.write(f"{Cursor.POS(1, input_row)}Enter {Fore.YELLOW}command{Style.RESET_ALL}: ")
            sys.stdout.flush()
            command = input().strip()
            clear_line(output_row)

            if command.startswith("go "):
                try:
                    # Extract percentage from command
                    percentage = int(command.split()[1])
                    if 0 <= percentage <= 100:
                        total_duration = player.get_length()
                        if total_duration > 0:
                            target_time = (total_duration * percentage) // 100
                            player.set_time(target_time)
                            sys.stdout.write(f"{Cursor.POS(1, output_row)}Video moved to {Fore.YELLOW}{percentage}%{Style.RESET_ALL}.\n")
                        else:
                            sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Unable to retrieve video duration. Please try again.\n")
                    else:
                        sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Percentage must be between 0 and 100.\n")
                except ValueError:
                    sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Invalid percentage value. Please enter a valid number.\n")

            elif command.startswith("v "):
                try:
                    # Extract volume from command
                    volume = int(command.split()[1])
                    if 0 <= volume <= 100:
                        player.audio_set_volume(volume)
                        sys.stdout.write(f"{Cursor.POS(1, output_row)}Volume set to {Fore.YELLOW}{volume}{Style.RESET_ALL}.\n")
                    else:
                        sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Volume must be between 0 and 100.\n")
                except ValueError:
                    sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Invalid volume value. Please enter a number between 1 and 100.\n")

            elif command == "p":
                # Toggle pause/resume
                if player.is_playing():
                    player.pause()  # Pause the video
                    sys.stdout.write(f"{Cursor.POS(1, output_row)}Video {Fore.YELLOW}paused{Style.RESET_ALL}.\n")
                else:
                    player.play()  # Resume the video
                    sys.stdout.write(f"{Cursor.POS(1, output_row)}Video {Fore.YELLOW}resumed{Style.RESET_ALL}.\n")

            elif command == "q":
                sys.stdout.write(f"{Cursor.POS(1, output_row)}Exiting video player...\n")
                player.stop()
                break  # Exit the loop and stop the video player

            else:
                sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Invalid command. Please enter a valid command.\n")

            sys.stdout.flush()
