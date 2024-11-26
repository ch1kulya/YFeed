import os
import sys
import json
import feedparser
import webbrowser
import re
from time import sleep
from colorama import Fore, Style, Cursor
from datetime import datetime
from typing import Dict, List, Set
from googleapiclient.errors import HttpError
from yt_dlp import YoutubeDL
import vlc
from tqdm import tqdm
from utils.settings import CONFIG_FILE, CHANNELS_FILE, WATCHED_FILE
from utils.extractor import YouTubeChannelExtractor

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
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        return hours * 3600 + minutes * 60 + seconds

    def fetch_videos(self, channel_id: str) -> List[Dict]:
        # Fetch videos for a channel
        try:
            # Fetch the feed data from the channel
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(url)

            # Collect all video IDs in the current feed
            video_ids = [entry.id.split(":")[-1] for entry in feed.entries]

            # Fetch details for all videos in a single request
            try:
                video_response = self.channel_extractor.youtube.videos().list(
                    part="contentDetails",
                    id=','.join(video_ids)
                ).execute()

                # Extract the duration from the response and filter videos
                min_seconds = self.config.get("min_video_length", 2) * 60
                videos = []
                
                for entry in feed.entries:
                    video_id = entry.id.split(":")[-1]
                    items = [item for item in video_response.get("items", []) if item["id"] == video_id]

                    if not items:
                        continue

                    duration = items[0]["contentDetails"]["duration"]
                    total_seconds = self.iso_duration_to_seconds(duration)

                    if total_seconds < min_seconds:
                        continue

                    videos.append({
                        "title": self.remove_emojis(entry.title),
                        "link": entry.link,
                        "published": datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z"),
                        "id": entry.id,
                        "author": entry.author if 'author' in entry else "Unknown",
                    })

                return videos
            except HttpError as e:
                print(Fore.RED + f"Error fetching video details: {e}")
                return []
        except Exception as e:
            print(Fore.RED + f"Error fetching videos for channel {channel_id}: {str(e)}")
            return []

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', 0)
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
        instance = vlc.Instance('--no-video-title-show', '--quiet')
        player = instance.media_player_new()

        # Load the video file into VLC player
        media = instance.media_new(video_file)
        player.set_media(media)
        player.set_fullscreen(False)
        player.audio_set_volume(50)

        # Play the video
        player.play()

        print(f"\n{Style.BRIGHT}Video Controls{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1.{Fore.WHITE} '{Fore.YELLOW}go{Fore.WHITE} [{Fore.YELLOW}seconds{Fore.WHITE}]'{Fore.LIGHTBLACK_EX} — Move to the given percentage of the video")
        print(f"{Fore.CYAN}2.{Fore.WHITE} '{Fore.YELLOW}v{Fore.WHITE} [{Fore.YELLOW}volume{Fore.WHITE}]'{Fore.LIGHTBLACK_EX} — Set volume (1 to 100)")
        print(f"{Fore.CYAN}3.{Fore.WHITE} '{Fore.YELLOW}q{Fore.WHITE}'{Fore.LIGHTBLACK_EX} — Quit the player{Style.RESET_ALL}")
        
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

            if command.startswith("go"):
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

            elif command.startswith("v"):
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

            elif command == "q":
                sys.stdout.write(f"{Cursor.POS(1, output_row)}Exiting video player...\n")
                player.stop()
                break  # Exit the loop and stop the video player

            else:
                sys.stdout.write(f"{Cursor.POS(1, output_row)}{Fore.RED}Invalid command. Please enter a valid command.\n")

            sys.stdout.flush()
