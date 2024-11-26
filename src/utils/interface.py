import os
import pyfiglet
from time import sleep
from datetime import datetime, timedelta
from colorama import Fore, Style
from utils.manager import YouTubeFeedManager
from utils.extractor import YouTubeChannelExtractor

class Interface:
    def __init__(self, manager: YouTubeFeedManager):
        self.manager = manager
        self.terminal_width = os.get_terminal_size().columns
        self.padding = 2

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

    def draw_logo(self) -> None:
        # Draw application logo
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
        # Input prompt
        return input(f"{Fore.CYAN}{prompt}: {Style.RESET_ALL}")

    def show_message(self, message: str, color: str = Fore.WHITE) -> None:
        # Display message
        print(f"{color}{message}{Style.RESET_ALL}")
        input(Fore.WHITE + f"Press {Fore.YELLOW}Enter{Fore.WHITE} to continue...")

    def main_menu(self) -> str:
        # Display main menu
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
        # Display videos list
        self.draw_logo()
        videos = []
        
        for channel_id in self.manager.channels:
            videos.extend(self.manager.fetch_videos(channel_id))
            print(Fore.GREEN + f"Videos from {channel_id} fetched!")
        
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
        print(Fore.GREEN + Style.BRIGHT + "All videos fetched!")
        sleep(0.4)
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
            
            cutoff_index = len(title)
            for char in ["|", "[", "("]:
                index = title.find(char)
                if 0 <= index < cutoff_index:
                    cutoff_index = index
                    
            title = title[:cutoff_index].strip()
                    
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
                f"{color}{str(idx + 1).rjust(index_width)} {Fore.CYAN}│{color} "
                f"{title.ljust(title_width)} {Fore.CYAN}│{color} "
                f"{channel_name.ljust(channel_width)} {Fore.CYAN}│{color} "
                f"{color_time}{time_ago.ljust(time_width)}{Style.RESET_ALL}"
            )

        choice = self.input_prompt(f"\n{Fore.WHITE}Select video {Fore.YELLOW}number{Fore.WHITE} or press {Fore.YELLOW}Enter{Fore.WHITE} to return")
        if choice.isdigit() and 1 <= int(choice) <= len(videos):
            video = videos[int(choice) - 1]
            self.manager.watched.add(video["id"])
            self.manager.save_watched()
            os.system("cls" if os.name == "nt" else "clear")
            self.draw_logo()
            manager = YouTubeFeedManager()
            manager.watch_video(video["link"])

    def channels_menu(self) -> None:
        # Display channels menu
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

                print(f"{Fore.CYAN}{'#'.center(2)} │ {'Channel ID'}{Style.RESET_ALL}")
                
                for idx, channel_id in enumerate(self.manager.channels, 1):
                    print(f"{str(idx).center(2)} │ {channel_id}")
                
                input(f"\n{Fore.WHITE}Press {Fore.YELLOW}Enter{Fore.WHITE} to return{Style.RESET_ALL}")

            elif choice == "3":
                if not self.manager.channels:
                    self.show_message("No channels to remove!", Fore.YELLOW)
                    continue

                self.draw_logo()
                
                print(f"{Fore.CYAN}{'#'.center(2)} │ {'Channel ID'}{Style.RESET_ALL}")
                
                for idx, channel_id in enumerate(self.manager.channels, 1):
                    print(f"{str(idx).center(2)} │ {channel_id}")
                
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
        # Display settings menu
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
