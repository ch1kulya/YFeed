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
import msvcrt
import concurrent.futures

def getch():
    """Get single symbol from keyboard without input."""
    try:
        # Windows
        return msvcrt.getch().decode()
    except ImportError:
        # TODO Linux/Mac Support
        pass

class Interface:
    """Manages the user interface for the YFeed application."""

    def __init__(self, manager: YouTubeFeedManager):
        """Initialize the Interface with a YouTubeFeedManager instance.

        Args:
            manager (YouTubeFeedManager): The manager instance to handle YouTube feeds.
        """
        self.manager = manager
        self.terminal_width = os.get_terminal_size().columns
        self.index_width = 2
        self.name_width = 30
        self.id_width = 26
        self.channel_ids = self.manager.channels
        self.channel_map = self.manager.channel_extractor.get_channel_names(self.channel_ids)
        self.separator = "═" * (self.index_width + 1) + "╪" + "═" * (self.name_width + 2) + "╪" + "═" * (self.id_width)

    def greet(self):
        """Display a greeting message with a gradient color effect and clear the screen after a pause.

        The greeting is based on the current time of day and is rendered using ASCII art with gradient colors.
        """
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
        """Center the given text horizontally in the terminal.

        Args:
            text (str): The text to be centered.

        Returns:
            str: The centered text with appropriate padding.
        """
        stripped_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        text_length = len(stripped_text)
        padding = (self.terminal_width - text_length) // 2
        return ' ' * max(padding, 0) + text
            
    def shut_down(self):
        """Perform cleanup actions and display a goodbye message.

        This method clears the terminal screen, deletes all .webm files in the current directory,
        and displays a goodbye message with a gradient color effect.
        """
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
        """Apply a gradient color effect to the given text.

        Args:
            text (str): The text to apply the gradient effect to.
            start_color (tuple): RGB values for the start color (e.g., (255, 200, 255)).
            end_color (tuple): RGB values for the end color (e.g., (255, 99, 255)).

        Returns:
            str: The text with ANSI escape codes applied for gradient coloring.
        """
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
        """Format a timedelta object into a human-readable 'time ago' string.

        Args:
            delta (timedelta): The time difference to format.

        Returns:
            str: A string representing the time difference, e.g., '5m ago', '2h ago', '1d ago'.
        """
        minutes = delta.total_seconds() / 60
        if minutes < 60:
            return f"{int(minutes)}m ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        return f"{int(hours / 24)}d ago"
    
    def draw_logo(self, text) -> None:
        """Display the application logo with a gradient color effect.

        Args:
            text (str): Additional text to display alongside the logo.

        This method clears the terminal screen, creates a logo with the specified text,
        applies a gradient color, and centers it on the screen.
        """
        os.system("cls" if os.name == "nt" else "clear")
        logo_text = "YFeed " + text
        logo = pyfiglet.figlet_format(logo_text, font='slant', width=self.terminal_width)
        gradient_logo = self.gradient_color(
            logo,
            (255, 255, 0),  # Yellow
            (255, 69, 0)    # Red-Orange
        )
        print(3 * "\n")
        for line in gradient_logo.split('\n'):
            print(self.center_text(line))
        print("\n")
    
    def input_prompt(self, prompt: str) -> str:
        """Display an input prompt to the user and return their input.

        Args:
            prompt (str): The prompt message to display to the user.

        Returns:
            str: The user's input as a string.
        """
        return input(f"{prompt}: {Style.RESET_ALL}")
    
    def show_message(self, message: str, color: str = Fore.WHITE) -> None:
        """Display a message to the user in a specified color and wait for them to press Enter.

        Args:
            message (str): The message to display.
            color (str, optional): The color to display the message in. Defaults to Fore.WHITE.
        """
        print(f"{color}{message}{Style.RESET_ALL}")
        input(Fore.WHITE + f"Press {Fore.YELLOW}Enter{Fore.WHITE} to continue...")
    
    def main_menu(self) -> str:
        """Display the main menu and prompt the user to make a selection.

        Returns:
            str: The user's menu selection as a string.
        """
        self.draw_logo("Home")
        options = [
            (f"{Fore.YELLOW}1{Fore.WHITE}. Fetch latest         {Fore.YELLOW}4{Fore.WHITE}. Subscribe            {Fore.YELLOW}7{Fore.WHITE}. Days filter  "),
            (f"{Style.DIM}{Fore.YELLOW}2{Fore.WHITE}. Search{Style.NORMAL}               {Fore.YELLOW}5{Fore.WHITE}. Channel list         {Fore.YELLOW}8{Fore.WHITE}. Length filter"),
            (f"{Style.DIM}{Fore.YELLOW}3{Fore.WHITE}. Live streams{Style.NORMAL}         {Fore.YELLOW}6{Fore.WHITE}. Unsubscribe          {Fore.YELLOW}9{Fore.WHITE}. Set API key  ")
        ]
    
        for option in options:
            print(self.center_text(option))
        print("\n")
        print(self.center_text(f"{Fore.WHITE}Press a number [{Fore.YELLOW}1{Fore.WHITE}-{Fore.YELLOW}9{Fore.WHITE}] to choose an [{Fore.YELLOW}option{Fore.WHITE}] or [{Fore.RED}q{Fore.WHITE}] to terminate "))
        print("\n")
        while True:
            selection = getch()
            if selection in '123456789q':
                return selection
        
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
                    print(f"{Fore.RED}Timeout{Fore.WHITE} on first attempt for channel {self.manager.channel_extractor.get_channel_names([channel_id]).get(channel_id, "Unknown")}.{Style.RESET_ALL} Retrying...")
                else:
                    print(f"{Fore.RED}Timeout{Fore.WHITE} on second attempt for channel {self.manager.channel_extractor.get_channel_names([channel_id]).get(channel_id, "Unknown")}.{Style.RESET_ALL} Giving up.")
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
    
    def videos_menu(self) -> None:
        """Display the videos menu, fetch latest videos, and handle user interactions.

        This method fetches the latest videos from the subscribed channels, displays them in a formatted list,
        and allows the user to select a video to watch.
        """
        self.draw_logo("Video List")
        videos = []
        fetching_start_time = time()
        print(f"Fetching videos from {Fore.YELLOW}{len(self.manager.channels)}{Fore.WHITE} channels!{Style.RESET_ALL}")
        print("Parsing...")
        parsed_feeds = self.parse_feeds(self.manager.channels)
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
    
                # TODO: Linux/Mac support

    def add_channel(self) -> None:
        """Add a YouTube channel to the manager."""
        if not self.manager.config.get('api_key'):
            self.show_message("Please set YouTube API key in settings first!", Fore.RED)
        link = self.input_prompt(f"{Fore.WHITE}Enter YouTube channel {Fore.YELLOW}link{Fore.WHITE}")
        if link.strip():
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


    def list_channels(self) -> None:
        """List all managed YouTube channels."""
        if not self.manager.channels:
            self.show_message("No channels added yet!", Fore.YELLOW)

        print(f"{Fore.CYAN}{'#'.center(self.index_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel Name'.ljust(self.name_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel ID'}{Style.RESET_ALL}")
        print(self.separator)
        for idx, channel_id in enumerate(self.channel_ids, 1):
            channel_name = self.channel_map.get(channel_id, "Unknown")
            print(f"{str(idx).center(self.index_width)} │ {channel_name.ljust(self.name_width)} │ {channel_id}")

        input(f"\n{Fore.WHITE}Press {Fore.YELLOW}Enter{Fore.WHITE} to return{Style.RESET_ALL}")


    def remove_channels(self) -> None:
        """Remove one or more YouTube channels from the manager."""
        while True:
            print(f"{Fore.CYAN}{'#'.center(self.index_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel Name'.ljust(self.name_width)} {Fore.WHITE}│{Fore.CYAN} {'Channel ID'}{Style.RESET_ALL}")
            print(self.separator)
            for idx, channel_id in enumerate(self.channel_ids, 1):
                channel_name = self.channel_map.get(channel_id, "Unknown")
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

    def days_filter(self) -> None:
        """Manage the filter for the number of days."""
        days = self.input_prompt(f"{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} of days" + f" (current - {self.manager.config['days_filter']} days)")
        if days.isdigit() and int(days) > 0:
            self.manager.config["days_filter"] = int(days)
            self.manager.save_config()
            self.show_message("Settings updated!", Fore.GREEN)
        elif days.strip():
            self.show_message("Invalid input.", Fore.RED)
            
    def length_filter(self) -> None:
        """Manage the minimum video length filter."""
        new_length = self.input_prompt(f"{Fore.WHITE}Enter {Fore.YELLOW}number{Fore.WHITE} of minutes" + f" (current {self.manager.config['min_video_length']} minutes)")
        if new_length.isdigit() and int(new_length) > 0:
            self.manager.config["min_video_length"] = int(new_length)
            self.manager.save_config()
            self.show_message("Settings updated!", Fore.GREEN)
        elif new_length.strip():
            self.show_message("Invalid input.", Fore.RED)

    def manage_api(self) -> None:
        """Manage the YouTube API key."""
        api_key = self.input_prompt(f"{Fore.WHITE}Enter YouTube {Fore.YELLOW}API Key{Fore.WHITE}" + f" (current {'*' * 8 if self.manager.config.get('api_key') else 'Not Set'})")
        if api_key.strip():
            self.manager.config["api_key"] = api_key.strip()
            self.manager.save_config()
            self.manager.channel_extractor = YouTubeChannelExtractor(api_key.strip())
            self.show_message("API Key updated!", Fore.GREEN)
        #elif api_key:
        #TODO api_key validation
    
    def search_menu(self) -> None:
        pass #TODO youtube search

    def live_menu(self) -> None:
        pass #TODO live streams menu