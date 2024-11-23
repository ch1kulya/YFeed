import os
import json
import feedparser
import webbrowser
import pyfiglet
import re
from colorama import Fore, Style, init, Back
from datetime import datetime, timedelta
from typing import Dict, List, Set
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

init(autoreset=True)

CONFIG_FILE = "data/settings.json"
CHANNELS_FILE = "data/channels.yfe"
WATCHED_FILE = "data/watched.yfe"

class YouTubeChannelExtractor:
    def __init__(self, api_key: str):
        """Initialize YouTube API client"""
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_channel_id(self, link: str) -> str:
        """Get channel ID from various YouTube URL formats"""
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
        """Get channel ID using YouTube Data API"""
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
        """Validate if channel ID exists"""
        try:
            response = self.youtube.channels().list(
                part="id",
                id=channel_id
            ).execute()
            return bool(response.get("items"))
        except HttpError:
            return False

class YouTubeFeedManager:
    def __init__(self):
        """Initialize the feed manager"""
        self.config = self.load_config()
        self.channels = self.load_channels()
        self.watched = self.load_watched()
        self.channel_extractor = None
        
        # Initialize API if key exists
        if self.config.get('api_key'):
            self.channel_extractor = YouTubeChannelExtractor(self.config['api_key'])

    @staticmethod
    def load_config() -> Dict:
        """Load configuration from file"""
        default_config = {"days_filter": 7, "api_key": "", "min_video_length": 2}
        if not os.path.exists(CONFIG_FILE):
            return default_config
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return {**default_config, **config}

    def save_config(self) -> None:
        """Save configuration to file"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    @staticmethod
    def load_channels() -> List[str]:
        """Load channel list from file"""
        if not os.path.exists(CHANNELS_FILE):
            return []
        with open(CHANNELS_FILE, "r") as f:
            return [line.strip() for line in f]

    def save_channels(self) -> None:
        """Save channel list to file"""
        os.makedirs(os.path.dirname(CHANNELS_FILE), exist_ok=True)
        with open(CHANNELS_FILE, "w") as f:
            f.write("\n".join(self.channels))

    @staticmethod
    def load_watched() -> Set[str]:
        """Load watched videos from file"""
        if not os.path.exists(WATCHED_FILE):
            return set()
        with open(WATCHED_FILE, "r") as f:
            return set(line.strip() for line in f)

    def save_watched(self) -> None:
        """Save watched videos to file"""
        os.makedirs(os.path.dirname(WATCHED_FILE), exist_ok=True)
        with open(WATCHED_FILE, "w") as f:
            f.write("\n".join(self.watched))
            
    @staticmethod
    def remove_emojis(text: str) -> str:
        """Remove emojis from text"""
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
        """Convert ISO 8601 duration format to total seconds"""
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        return hours * 3600 + minutes * 60 + seconds

    def fetch_videos(self, channel_id: str) -> List[Dict]:
        """Fetch videos for a channel, filter by length, and remove emojis"""
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

class Interface:
    def __init__(self, manager: YouTubeFeedManager):
        self.manager = manager
        self.terminal_width = os.get_terminal_size().columns
        self.padding = 2

    def gradient_color(self, text: str, start_color: tuple, end_color: tuple) -> str:
        """Create a gradient effect for text"""
        result = ""
        for i, char in enumerate(text):
            if char == '\n':
                result += char
                continue
            r = int(start_color[0] + (end_color[0] - start_color[0]) * i / len(text))
            g = int(start_color[1] + (end_color[1] - start_color[1]) * i / len(text))
            b = int(start_color[2] + (end_color[2] - start_color[2]) * i / len(text))
            result += f"\033[38;2;{r};{g};{b}m{char}"
        return result + Style.RESET_ALL

    def format_time_ago(self, delta: timedelta) -> str:
        """Format timedelta into human readable string"""
        minutes = delta.total_seconds() / 60
        if minutes < 60:
            return f"{int(minutes)}m ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        return f"{int(hours / 24)}d ago"

    def draw_logo(self) -> None:
        """Draw application logo with gradient effect"""
        os.system("cls" if os.name == "nt" else "clear")
        logo = pyfiglet.figlet_format("YFeed", font='slant', width=self.terminal_width)
        gradient_logo = self.gradient_color(
            logo,
            (255, 255, 0),  # Yellow
            (255, 69, 0)    # Red-Orange
        )
        print("\n")
        for line in gradient_logo.split('\n'):
            print(" " * 3 + line)
        print("\n")

    def input_prompt(self, prompt: str) -> str:
        """Styled input prompt"""
        return input(f"{Fore.CYAN}{prompt}: {Style.RESET_ALL}")

    def show_message(self, message: str, color: str = Fore.WHITE) -> None:
        """Display message without excessive spacing"""
        print(f"{color}{message}{Style.RESET_ALL}")
        input(Fore.WHITE + f"Press {Fore.YELLOW}Enter{Fore.WHITE} to continue...")

    def main_menu(self) -> str:
        """Display main menu"""
        self.draw_logo()
        options = [
            ("1", "Videos", "- Browse latest videos from your subscriptions"),
            ("2", "Channels", "- Manage your channel subscriptions"),
            ("3", "Settings", "- Configure application settings"),
            ("4", "Exit", "")
        ]

        for num, title, desc in options:
            print(f"{Fore.CYAN}{num}. {Fore.WHITE}{title} {Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")

        return self.input_prompt(f"\nChoose an {Style.BRIGHT}option{Style.NORMAL}")

    def videos_menu(self) -> None:
        """Display videos menu"""
        self.draw_logo()
        videos = []
        
        for channel_id in self.manager.channels:
            videos.extend(self.manager.fetch_videos(channel_id))
            print(Fore.GREEN + "Video fetched!")
        
        if not videos:
            self.show_message("No videos found!", Fore.RED)
            return

        videos = sorted(videos, key=lambda x: x["published"], reverse=True)
        cutoff_date = datetime.now(videos[0]["published"].tzinfo) - timedelta(days=self.manager.config["days_filter"])
        videos = [video for video in videos if video["published"] > cutoff_date]

        index_width = len(str(len(videos)))
        time_width = 12
        channel_width = 18
        remaining_width = self.terminal_width - (index_width + time_width + channel_width)
        title_width = int(remaining_width * 0.9)

        header = (
            f"{Fore.CYAN}{Style.BRIGHT}{'#'.ljust(index_width)} │ "
            f"{'Title'.ljust(title_width)} │ "
            f"{'Channel'.ljust(channel_width)} │ "
            f"{'Published'.ljust(time_width)}{Style.RESET_ALL}"
        )
        os.system("cls" if os.name == "nt" else "clear")
        self.draw_logo()
        print(header)

        for idx, video in enumerate(videos):
            title = video["title"]
            published = video["published"]
            delta = datetime.now(published.tzinfo) - published
            time_ago = self.format_time_ago(delta)

            channel_name = video.get("author", "Unknown Channel")
            if len(channel_name) > channel_width - 3:
                channel_name = channel_name[:channel_width-3] + "..."

            if len(title) > title_width - 3:
                title = title[:title_width-3] + "..."

            if video["id"] in self.manager.watched:
                color = Fore.LIGHTBLACK_EX
                color_time = Fore.LIGHTBLACK_EX
            elif delta.days == 0:
                color = Fore.WHITE
                color_time = Fore.LIGHTMAGENTA_EX
            else:
                color = Fore.WHITE
                color_time = Fore.WHITE

            print(
                f"{color}{str(idx + 1).rjust(index_width)} │ "
                f"{title.ljust(title_width)} │ "
                f"{channel_name.ljust(channel_width)} │ "
                f"{color_time}{time_ago.ljust(time_width)}{Style.RESET_ALL}"
            )

        choice = self.input_prompt(f"\n{Fore.WHITE}Select video {Fore.YELLOW}number{Fore.WHITE} or press {Fore.YELLOW}Enter{Fore.WHITE} to return")
        if choice.isdigit() and 1 <= int(choice) <= len(videos):
            video = videos[int(choice) - 1]
            self.manager.watched.add(video["id"])
            self.manager.save_watched()
            webbrowser.open(video["link"])

    def channels_menu(self) -> None:
        """Display channels menu"""
        while True:
            self.draw_logo()
            
            options = [
                ("1", "Add Channel", "- Add a new YouTube channel to follow"),
                ("2", "View Channels", "- List all subscribed channels"),
                ("3", "Remove Channel", "- Unsubscribe from a channel"),
                ("4", "Return", "")
            ]

            for num, title, desc in options:
                print(f"{Fore.CYAN}{num}. {Fore.WHITE}{title} {Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")

            choice = self.input_prompt(f"\nChoose an {Style.BRIGHT}option{Style.NORMAL}")

            if choice == "1":
                if not self.manager.config.get('api_key'):
                    self.show_message("Please set YouTube API key in settings first!", Fore.RED)
                    continue
                    
                link = self.input_prompt(f"{Fore.WHITE}\nEnter YouTube channel {Fore.YELLOW}link{Fore.WHITE}")
                try:
                    channel_id = self.manager.channel_extractor.get_channel_id(link)
                    if channel_id not in self.manager.channels:
                        self.manager.channels.append(channel_id)
                        self.manager.save_channels()
                        self.show_message("Channel added successfully!", Fore.GREEN)
                    else:
                        self.show_message("Channel already exists.", Fore.YELLOW)
                except Exception as e:
                    self.show_message(f"Error: {str(e)}", Fore.RED)

            elif choice == "2":
                self.draw_logo()
                
                if not self.manager.channels:
                    self.show_message("No channels added yet!", Fore.YELLOW)
                    continue

                print(f"{Fore.CYAN}{Style.BRIGHT}{'#'.center(4)} │ {'Channel ID'}{Style.RESET_ALL}")
                
                for idx, channel_id in enumerate(self.manager.channels, 1):
                    print(f"{str(idx).center(4)} │ {channel_id}")
                
                input(f"\n{Fore.WHITE}Press {Fore.YELLOW}Enter{Fore.WHITE} to return{Style.RESET_ALL}")

            elif choice == "3":
                if not self.manager.channels:
                    self.show_message("No channels to remove!", Fore.YELLOW)
                    continue

                self.draw_logo()
                
                print(f"{Fore.CYAN}{'#'.center(4)} │ {'Channel ID'}{Style.RESET_ALL}")
                
                for idx, channel_id in enumerate(self.manager.channels, 1):
                    print(f"{str(idx).center(4)} │ {channel_id}")
                
                choice = self.input_prompt(f"\n{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} to remove or press {Fore.YELLOW}Enter{Fore.WHITE} to cancel")
                
                if choice.isdigit() and 1 <= int(choice) <= len(self.manager.channels):
                    removed = self.manager.channels.pop(int(choice) - 1)
                    self.manager.save_channels()
                    self.show_message(f"Removed channel: {removed}", Fore.GREEN)

            elif choice == "4":
                break
            else:
                self.show_message("Invalid choice!", Fore.RED)

    def settings_menu(self) -> None:
        """Display settings menu"""
        while True:
            self.draw_logo()
            options = [
                ("1", "Days Filter", f"- Current: {self.manager.config['days_filter']}"),
                ("2", "Minimum Video Length", f"- Current: {self.manager.config['min_video_length']} minutes"),
                ("3", "YouTube API Key", f"- Current: {'*' * 8 if self.manager.config.get('api_key') else 'Not Set'}"),
                ("4", "Return", "")
            ]

            for num, title, desc in options:
                print(f"{Fore.CYAN}{num}. {Fore.WHITE}{title} {Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")
            choice = self.input_prompt(f"\nChoose an {Style.BRIGHT}option{Style.NORMAL}")

            if choice == "1":
                days = self.input_prompt(f"{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} of days")
                if days.isdigit() and int(days) > 0:
                    self.manager.config["days_filter"] = int(days)
                    self.manager.save_config()
                    print(Fore.GREEN + "Settings updated!")
                else:
                    print(Fore.RED + "Invalid input.")
                input(Fore.WHITE + f"\nPress {Fore.YELLOW}Enter{Fore.WHITE} to continue...")
                
            elif choice == "2":
                new_length = self.input_prompt(f"{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} of minutes")
                if new_length.isdigit() and int(new_length) > 0:
                    self.manager.config["min_video_length"] = int(new_length)
                    self.manager.save_config()
                    print(Fore.GREEN + "Settings updated!")
                else:
                    print(Fore.RED + "Invalid input.")
                input(Fore.WHITE + f"\nPress {Fore.YELLOW}Enter{Fore.WHITE} to continue...")

            elif choice == "3":
                api_key = self.input_prompt(f"{Fore.WHITE}Enter YouTube {Fore.YELLOW}API Key{Fore.WHITE}")
                if api_key.strip():
                    self.manager.config["api_key"] = api_key.strip()
                    self.manager.save_config()
                    self.manager.channel_extractor = YouTubeChannelExtractor(api_key.strip())
                    print(Fore.GREEN + "API Key updated!")
                else:
                    print(Fore.RED + "Invalid API Key.")
                input(Fore.WHITE + f"\nPress {Fore.YELLOW}Enter{Fore.WHITE} to continue...")

            elif choice == "4":
                break
            else:
                self.show_message("Invalid choice!", Fore.RED)

def main():
    """Main application entry point"""
    manager = YouTubeFeedManager()
    interface = Interface(manager)

    while True:
        choice = interface.main_menu()
        if choice == "1":
            interface.videos_menu()
        elif choice == "2":
            interface.channels_menu()
        elif choice == "3":
            interface.settings_menu()
        elif choice == "4":
            print(Fore.YELLOW + Style.BRIGHT + "Goodbye!")
            break
        else:
            interface.show_message("Invalid choice!", Fore.RED)

if __name__ == "__main__":
    main()
