import os
import glob
import shutil
import pyfiglet
from time import sleep, time
from datetime import datetime, timedelta
from colorama import Fore, Style
from utils.manager import YouTubeFeedManager
from utils.extractor import YouTubeChannelExtractor
from utils.settings import TIMEOUT_SECONDS
import subprocess
import feedparser
import requests
import re
import concurrent.futures

class Interface:
    def __init__(self, manager: YouTubeFeedManager):
        self.manager = manager
        self.terminal_width = os.get_terminal_size().columns
        
    def greet(self):
        greeting = f"Good {['Night', 'Morning', 'Afternoon', 'Evening'][(datetime.now().hour // 6)]}!"
        greeting_art = pyfiglet.figlet_format(greeting, font='slant', width=self.terminal_width)
        gradient_art = self.gradient_color(
            greeting_art,
            (255, 200, 255),
            (255, 99, 255)
        )
        print("\n")
        for line in gradient_art.split('\n'):
            print(self.center_text(line))
        print("\n")
        sleep(1.5)
        os.system("cls" if os.name == "nt" else "clear")
            
    def center_text(self, text):
        stripped_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        text_length = len(stripped_text)
        padding = (self.terminal_width - text_length) // 2
        return ' ' * max(padding, 0) + text
        
    def shut_down(self):
        os.system("cls" if os.name == "nt" else "clear")
        webm_files = glob.glob(os.path.join(".", "*.webm"))
        for file in webm_files:
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")
        goodbye_art = pyfiglet.figlet_format("Goodbye!", font='slant', width=self.terminal_width)
        gradient_art = self.gradient_color(
            goodbye_art,
            (255, 255, 255),
            (255, 69, 255)
        )
        print("\n")
        for line in gradient_art.split('\n'):
            print(self.center_text(line))
        print("\n")

    def gradient_color(self, text: str, start_color: tuple, end_color: tuple) -> str:
        # Create a gradient effect for text
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
        # Format timedelta into human readable string"
        minutes = delta.total_seconds() / 60
        if minutes < 60:
            return f"{int(minutes)}m ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        return f"{int(hours / 24)}d ago"

    def draw_logo(self, text) -> None:
        # Draw application logo
        os.system("cls" if os.name == "nt" else "clear")
        logo_text = "YFeed " + text
        logo = pyfiglet.figlet_format(logo_text, font='slant', width=self.terminal_width)
        gradient_logo = self.gradient_color(
            logo,
            (255, 255, 0),  # Yellow
            (255, 69, 0)    # Red-Orange
        )
        print("\n")
        for line in gradient_logo.split('\n'):
            print(self.center_text(line))
        print("\n")

    def input_prompt(self, prompt: str) -> str:
        # Input prompt
        return input(f"{prompt}: {Style.RESET_ALL}")

    def show_message(self, message: str, color: str = Fore.WHITE) -> None:
        # Display message
        print(f"{color}{message}{Style.RESET_ALL}")
        input(Fore.WHITE + f"Press {Fore.YELLOW}Enter{Fore.WHITE} to continue...")

    def main_menu(self) -> str:
        # Display main menu
        self.draw_logo("Home")
        options = [
            ("1", "Videos", "- Fetch latest videos"),
            ("2", "Channels", "- Control subscriptions"),
            ("3", "Settings", "- Manage configuration"),
            ("4", "Exit", "- Terminate & Cleanup")
        ]

        for num, title, desc in options:
            print(f"{Fore.CYAN}{num}. {Fore.WHITE}{title} {Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")

        return self.input_prompt(f"\n{Fore.WHITE}Choose an {Fore.YELLOW}option{Fore.WHITE}")

    def videos_menu(self) -> None:
        # Display videos list
        self.draw_logo("Video List")
        videos = []
        fetching_start_time = time()
        print(f"Fetching videos from {Fore.YELLOW}{len(self.manager.channels)}{Fore.WHITE} channels!{Style.RESET_ALL}")
        
        def parse_feed(channel_id):
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            
            for attempt in range(3):
                try:
                    response = requests.get(url, timeout=TIMEOUT_SECONDS)
                    feed = feedparser.parse(response.content)
                    return feed
                except requests.exceptions.Timeout:
                    print(f"{Fore.RED}Timeout{Fore.WHITE} on attempt {Fore.RED}{attempt + 1}{Style.RESET_ALL}")
                    print("Retrying in 3...")
                    sleep(1)
                    print("Retrying in 2...")
                    sleep(1)
                    print("Retrying in 1...")
                    sleep(1)
                    if attempt == 2:
                        return None
                except Exception as e:
                    print(f"{Fore.RED}Error parsing {channel_id}: {Fore.WHITE}{e}{Style.RESET_ALL}")
                    return None

        def parse_feeds(channel_ids):
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(parse_feed, channel_ids))
            return results

        print("Parsing...")
        parsed_feeds = parse_feeds(self.manager.channels)
        print("Parsed successfully.")
        print("Fetching...")

        for i, channel_id in enumerate(self.manager.channels):
            feed = parsed_feeds[i]
            videos.extend(self.manager.fetch_videos(channel_id, feed))
            
        print("Fetched successfully.")
            
        if not videos:
            self.show_message("No videos found!", Fore.RED)
            return

        videos = sorted(videos, key=lambda x: x["published"], reverse=True)
        cutoff_date = datetime.now(videos[0]["published"].tzinfo) - timedelta(days=self.manager.config["days_filter"])
        videos = [video for video in videos if video["published"] > cutoff_date]

        index_width = len(str(len(videos)))
        time_width = 10
        channel_width = 25
        remaining_width = self.terminal_width - (index_width + time_width + channel_width)
        title_width = int(remaining_width * 0.9)
        separator = "═" * (index_width + 1) + "╪" + "═" * (title_width + 2) + "╪" + "═" * (channel_width + 2) + "╪" + "═" * (time_width)
        header = (
            f"{Fore.CYAN}{'#'.ljust(index_width)} {Fore.WHITE}│{Fore.CYAN} "
            f"{'Title'.ljust(title_width)} {Fore.WHITE}│{Fore.CYAN} "
            f"{'Channel'.ljust(channel_width)} {Fore.WHITE}│{Fore.CYAN} "
            f"{'Published'.ljust(time_width)}{Style.RESET_ALL}"
        )
        print(Fore.GREEN + Style.BRIGHT + "All videos fetched!")
        fetching_time = (time() - fetching_start_time) * 1000
        print(f"Total fetching time: {Fore.LIGHTRED_EX if fetching_time > 10000 else Fore.LIGHTGREEN_EX}{int(fetching_time)}{Style.RESET_ALL} ms")
        sleep(0.3)
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            self.draw_logo("Video List")
            print(header)
            print(separator)

            for idx, video in enumerate(videos):
                title = video["title"]
                published = video["published"]
                delta = datetime.now(published.tzinfo) - published
                time_ago = self.format_time_ago(delta)

                channel_name = video.get("author", "Unknown Channel")
                if len(channel_name) > channel_width - 3:
                    channel_name = channel_name[:channel_width-3] + "..."
                
                cutoff_index = len(title)
                for char in ["|", "[", "(", ".", "@"]:
                    index = title.find(char)
                    if 0 <= index < cutoff_index:
                        cutoff_index = index
                        
                title = " ".join(title[:cutoff_index].split())
                        
                if len(title) > title_width - 3:
                    title = title[:title_width-3] + "..."

                if video["id"] in self.manager.watched:
                    color = Fore.LIGHTBLACK_EX
                    color_time = Fore.LIGHTBLACK_EX
                elif delta.days == 0:
                    color = Fore.WHITE
                    color_time = Fore.LIGHTYELLOW_EX
                elif delta.days == 1:
                    color = Fore.WHITE
                    color_time = Fore.LIGHTMAGENTA_EX
                else:
                    color = Fore.WHITE
                    color_time = Fore.WHITE

                print(
                    f"{str(idx + 1).rjust(index_width)} {Fore.WHITE}│{color} "
                    f"{title.ljust(title_width)} {Fore.WHITE}│{color} "
                    f"{channel_name.ljust(channel_width)} {Fore.WHITE}│{color} "
                    f"{color_time}{time_ago.ljust(time_width)}{Style.RESET_ALL}"
                )

            choice = self.input_prompt(f"\n{Fore.WHITE}Select video {Fore.YELLOW}number{Fore.WHITE} or press {Fore.YELLOW}Enter{Fore.WHITE} to return")
            if not choice.strip():
                break
            if choice.isdigit() and 1 <= int(choice) <= len(videos):
                video = videos[int(choice) - 1]
                self.manager.watched.add(video["id"])
                self.manager.save_watched()
                if os.name == "nt":  # Windows
                    if shutil.which("wt.exe"):
                        subprocess.Popen(f'wt.exe -w 0 new-tab -- python src/instance.py "{video["link"]}"', shell=True)
                    else:
                        subprocess.Popen(f'start cmd /C python src/instance.py "{video["link"]}"', shell=True)

                #TODO Linux/Mac support

    def channels_menu(self) -> None:
        # Display channels menu
        while True:
            self.draw_logo("Channels")
            index_width = 2
            name_width = 30
            id_width = 26
            channel_ids = self.manager.channels
            channel_map = self.manager.channel_extractor.get_channel_names(channel_ids)
            separator = "═" * (index_width + 1) + "╪" + "═" * (name_width + 2) + "╪" + "═" * (id_width)

            options = [
                ("1", "Add Channel", "- Subscribe"),
                ("2", "View Channels", f"- Current: {len(channel_ids)}"),
                ("3", "Remove Channel", "- Unsubscribe"),
                ("4", "Return", "")
            ]

            for num, title, desc in options:
                print(f"{Fore.CYAN}{num}. {Fore.WHITE}{title} {Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")

            choice = self.input_prompt(f"\n{Fore.WHITE}Choose an {Fore.YELLOW}option{Fore.WHITE}")

            if choice == "1":
                if not self.manager.config.get('api_key'):
                    self.show_message("Please set YouTube API key in settings first!", Fore.RED)
                    continue
                
                print(f"\nPress {Fore.YELLOW}Enter{Fore.WHITE} to stop adding.")

                while True:
                    link = self.input_prompt(f"{Fore.WHITE}Enter YouTube channel {Fore.YELLOW}link{Fore.WHITE}")
                    if not link.strip():
                        break

                    try:
                        channel_id = self.manager.channel_extractor.get_channel_id(link)
                        if channel_id not in self.manager.channels:
                            self.manager.channels.append(channel_id)
                            self.manager.save_channels()
                            print(Fore.GREEN + "Channel added successfully!")
                        else:
                            self.show_message("Channel already exists.", Fore.YELLOW)
                    except Exception as e:
                        self.show_message(f"Error: {str(e)}", Fore.RED)

            elif choice == "2":
                self.draw_logo("Channels")

                if not self.manager.channels:
                    self.show_message("No channels added yet!", Fore.YELLOW)
                    continue

                print(f"{Fore.CYAN}{'#'.center(index_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel Name'.ljust(name_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel ID'}{Style.RESET_ALL}")
                print(separator)
                for idx, channel_id in enumerate(channel_ids, 1):
                    channel_name = channel_map.get(channel_id, "Unknown")
                    print(f"{str(idx).center(index_width)} │ {channel_name.ljust(name_width)} │ {channel_id}")

                input(f"\n{Fore.WHITE}Press {Fore.YELLOW}Enter{Fore.WHITE} to return{Style.RESET_ALL}")

            elif choice == "3":
                if not self.manager.channels:
                    self.show_message("No channels to remove!", Fore.YELLOW)
                    continue

                while True:
                    self.draw_logo("Channels")
                    print(f"{Fore.CYAN}{'#'.center(index_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel Name'.ljust(name_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel ID'}{Style.RESET_ALL}")
                    print(separator)
                    for idx, channel_id in enumerate(channel_ids, 1):
                        channel_name = channel_map.get(channel_id, "Unknown")
                        print(f"{str(idx).center(2)} │ {channel_name.ljust(30)} │ {channel_id}")
                        
                    print(f"\nPress {Fore.YELLOW}Enter{Fore.WHITE} to cancel or", end=" ")

                    choice = self.input_prompt(
                        f"{Fore.WHITE}enter {Fore.YELLOW}number{Fore.WHITE} to remove"
                    )

                    if not choice.strip():
                        break

                    if choice.isdigit() and 1 <= int(choice) <= len(self.manager.channels):
                        removed = self.manager.channels.pop(int(choice) - 1)
                        self.manager.save_channels()
                        print(f"{Fore.GREEN}Removed channel:{Fore.WHITE} {removed}")
                    else:
                        self.show_message("Invalid choice! Please enter a valid number.", Fore.RED)

                    if not self.manager.channels:
                        self.show_message("No more channels to remove!", Fore.YELLOW)
                        break

            elif choice == "4":
                break
            else:
                self.show_message("Invalid choice!", Fore.RED)

    def settings_menu(self) -> None:
        # Display settings menu
        while True:
            self.draw_logo("Settings")
            options = [
                ("1", "Days Filter", f"- Current: {self.manager.config['days_filter']} days"),
                ("2", "Minimum Length", f"- Current: {self.manager.config['min_video_length']} minutes"),
                ("3", "YouTube API Key", f"- Current: {'*' * 8 if self.manager.config.get('api_key') else 'Not Set'}"),
                ("4", "Return", "")
            ]

            for num, title, desc in options:
                print(f"{Fore.CYAN}{num}. {Fore.WHITE}{title} {Fore.LIGHTBLACK_EX}{desc}{Style.RESET_ALL}")
            choice = self.input_prompt(f"\n{Fore.WHITE}Choose an {Fore.YELLOW}option{Fore.WHITE}")

            if choice == "1":
                days = self.input_prompt(f"{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} of days")
                if days.isdigit() and int(days) > 0:
                    self.manager.config["days_filter"] = int(days)
                    self.manager.save_config()
                    self.show_message("Settings updated!", Fore.GREEN)
                else:
                    self.show_message("Invalid input.", Fore.RED)
                
            elif choice == "2":
                new_length = self.input_prompt(f"{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} of minutes")
                if new_length.isdigit() and int(new_length) > 0:
                    self.manager.config["min_video_length"] = int(new_length)
                    self.manager.save_config()
                    self.show_message("Settings updated!", Fore.GREEN)
                else:
                    self.show_message("Invalid input.", Fore.RED)

            elif choice == "3":
                api_key = self.input_prompt(f"{Fore.WHITE}Enter YouTube {Fore.YELLOW}API Key{Fore.WHITE}")
                if api_key.strip():
                    self.manager.config["api_key"] = api_key.strip()
                    self.manager.save_config()
                    self.manager.channel_extractor = YouTubeChannelExtractor(api_key.strip())
                    self.show_message("API Key updated!", Fore.GREEN)
                else:
                    self.show_message("Invalid API Key.", Fore.RED)

            elif choice == "4":
                break
            else:
                self.show_message("Invalid choice!", Fore.RED)
