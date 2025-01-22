import os
import re
import sys
import glob
import pyfiglet
from time import sleep
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
from utils.manager import FeedManager
from utils.extractor import Extractor
from rich.console import Console
from rich.padding import Padding
from rich.prompt import Prompt
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.markdown import Markdown
from rich import box

def getch():
    """Get single symbol from keyboard without input."""
    try:
        import msvcrt
        # Windows
        return msvcrt.getch().decode('utf-8', errors='ignore')
    except ImportError:
        import tty
        import termios
        # Linux/MacOS
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class Interface:
    """Manages the user interface for the YFeed application."""

    def __init__(self, manager: FeedManager):
        """Initialize the Interface with a FeedManager instance.

        Args:
            manager (FeedManager): The manager instance to handle YouTube feeds.
        """
        self.console = Console()
        self.manager = manager
        self.channel_ids = self.manager.channels
        self.channel_map = {}
        if  self.channel_ids:
           if self.manager.channel_extractor:
               self.channel_map = self.manager.channel_extractor.get_channel_names(self.channel_ids)

    def greet(self):
        """Display a greeting message with a gradient color effect and clear the screen after a pause.

        The greeting is based on the current time of day and is rendered using ASCII art with gradient colors.
        """
        greeting = f"Good {['Night', 'Morning', 'Afternoon', 'Evening'][(datetime.now().hour // 6)]}!"
        greeting_art = pyfiglet.figlet_format(greeting, font='slant')
        gradient_art = self.gradient_color(greeting_art, (255, 200, 255), (255, 99, 255))
        for line in gradient_art.split('\n'):
            print(line)
        sleep(0.7)
        os.system("cls" if os.name == "nt" else "clear")
            
    def shut_down(self):
        """Perform cleanup actions and display a goodbye message.

        This method clears the terminal screen, deletes all .webm files in the current directory,
        and displays a goodbye message with a gradient color effect.
        """
        os.system("cls" if os.name == "nt" else "clear")
        webm_files = glob.glob(os.path.join(".", "*.webm"))
        if webm_files:
            for file in webm_files:
                try:
                    os.remove(file)
                    self.console.print(f"Deleted: {file}")
                except Exception as e:
                    self.console.print(f"Error deleting {file}: {e}")
        else:
            self.console.print("Nothing to clean.\n")
        goodbye_art = pyfiglet.figlet_format("Goodbye!", font='slant')
        gradient_art = self.gradient_color(goodbye_art, (255, 255, 255), (255, 69, 255))
        for line in gradient_art.split('\n'):
            print(line)
    
    def format_title(self, title: str) -> str:
        """Perform title clean up.
        
        Args:
            text (str): The text to format.

        Returns:
            str: Cleared title.
        """
        cutoff_index = len(title)
        for char in ["|", "[", "(", ".", "@", ": ", "•", "+", "?", "/", ",", "-", " and ", "&", " и "]:
            index, addition = title.find(char), ""
            if 16 <= index < cutoff_index:
                cutoff_index = index
                if char in [".", "?"]:
                    addition = char
        title = " ".join(title[:cutoff_index].split()) + addition
        return title
    
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
            result += "\033[0m"
        return result
    
    def format_time_ago(self, delta: timedelta) -> str:
        """Format a timedelta object into a human-readable 'time ago' string.

        Args:
            delta (timedelta): The time difference to format.

        Returns:
            str: A string representing the time difference, e.g., '5m ago', '2h ago', '1d ago'.
        """
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}s ago"
        minutes = delta.total_seconds() / 60
        if minutes < 60:
            return f"{int(minutes)}m ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        days = hours / 24
        if days < 365:
            return f"{int(days)}d ago"
        return f"{int(days / 365)}y ago"
    
    def draw_heading(self, text) -> None:
        """Display the heading.

        Args:
            text (str): Text to display.

        This method clears the terminal screen, creates a heading with the specified text.
        """
        os.system("cls" if os.name == "nt" else "clear")
        self.console.print(Padding(Markdown(f"## {text}", style="b white"), (2, 30, 1, 30), expand=False))
    
    def show_message(self, message: str, color: str = "white") -> None:
        """Display a message to the user in a specified color and wait for them to press F.

        Args:
            message (str): The message to display.
            color (str, optional): The color to display the message in.
        """
        panel = Panel(Align.center(Padding(f"[{color}]{message}[/{color}]", (2, 5), expand=False), vertical="middle"), title="Message", subtitle="Press [b yellow]F[/b yellow] to continue", expand=True)
        self.console.print(Align.center(Padding(panel, (0, 2), expand=False), vertical="middle"))
        while True:
            selection = getch()
            if selection == 'f':
                return
    
    def main_menu(self) -> str:
        """Display the main menu and prompt the user to make a selection.

        Returns:
            str: The user's menu selection as a string.
        """
        self.draw_heading("Home")
        table = Table(box=box.ROUNDED, header_style="bold magenta")
        table.add_column("[white]Bind", justify="center")
        table.add_column("Option", justify="center", style="b white")
        table.add_column("Description", style="dim")
        table.add_row("1", "Fetch", "Fetches the latest released videos that match the filters from your channels.")
        table.add_row("2", "Search", "Searches for videos on YouTube based on your search query. Only the length filter works here.")
        table.add_row("3", "History", "Shows your watched videos with a time stamp. Allows you to rewatch already viewed ones.")
        table.add_row("4", "Subscribe", "Adds a new channel via link or handle to the managed list.")
        table.add_row("5", "Subscriptions", "Used to get a list of channels to which you are subscribed with information about them.")
        table.add_row("6", "Unsubscribe", "Allows you to remove an unnecessary channel from the managed list.")
        table.add_row("7", "Days filter", "Required to filter video novelty in days.")
        table.add_row("8", "Length filter", "Sets the minimum video length in minutes. Videos below the value will not be allowed.")
        table.add_row("9", "Set API key", "Manages your API key. Instructions for obtaining an API key can be found in the README.")
        table.add_row("[red]q", "Shutdown", "Correctly closes the program and cleans all downloaded videos.")
        self.console.print(Align.center(table, vertical="middle"))    
        self.console.print("\n" + " " * 9 + "Click the appropriate [underline]button[/underline] to select an option.")
        while True:
            selection = getch()
            if selection in '123456789q':
                return selection
    
    def videos_menu(self) -> None:
        """Display the videos menu, fetch latest videos, and handle user interactions.

        This method fetches the latest videos from the subscribed channels, displays them in a formatted list,
        and allows the user to select a video to watch.
        """
        if self.manager.channels:
            self.draw_heading("Video Fetcher")
            videos = []
            parsed_feeds = self.manager.parse_feeds(self.manager.channels)
            with self.console.status(" " * 9 + "[b green]Fetching videos..."):
                for i, channel_id in enumerate(self.manager.channels):
                    feed = parsed_feeds[i]
                    videos.extend(self.manager.fetch_videos(channel_id, feed))
            if not videos:
                self.draw_heading("Video Fetcher")
                self.show_message("No videos found!\nCheck your subscriptions and internet connection.", "red")
                return
            videos = sorted(videos, key=lambda x: x["published"], reverse=True)
            cutoff_date = datetime.now(videos[0]["published"].tzinfo) - timedelta(days=self.manager.config["days_filter"])
            videos = [video for video in videos if video["published"] > cutoff_date]
            if not videos:
                self.draw_heading("Video Fetcher")
                self.show_message("No videos found!\nCheck your filters and internet connection.", "red")
                return
            self.manager._log(f"[b green]Fetched successfully.")
            sleep(0.3)
            while True:
                self.draw_heading("Video List")
                table = Table(box=box.ROUNDED, header_style="bold magenta")
                table.add_column("[white]#", justify="center")
                table.add_column("Title")
                table.add_column("Channel", justify="center", style="b")
                table.add_column("Duration", justify="right", style="b")
                table.add_column("Published", justify="right", style="italic")
                for idx, video in enumerate(videos):
                    title = self.format_title(video["title"])
                    color, color_time = "white", "white"
                    published = video["published"]
                    delta = datetime.now(published.tzinfo) - published
                    time_ago = self.format_time_ago(delta)
                    channel_name = video.get("author", "Unknown Channel")
                    duration = f"{round(video['duration_seconds'] / 60)} min"
                    watched_videos = [dict(watched_video) for watched_video in self.manager.watched]
                    if any(video["id"] == watched_video["id"] for watched_video in watched_videos):
                        color = "dim"
                        color_time = "dim"
                    elif delta.days == 0:
                        color_time = "yellow"
                    elif delta.days == 1:
                        color_time = "magenta"
                    table.add_row(f"[{color}]{str(idx + 1)}[/{color}]", f"[{color}]{title}[/{color}]", f"[{color}]{channel_name}[/{color}]", f"[{color}]{duration}[/{color}]", f"[{color_time}]{time_ago}[/{color_time}]")
                self.console.print(Align.center(table, vertical="middle"))
                choice = Prompt.ask("\n" + " " * 9 + "Select video [underline]index[/underline] to watch or [underline]0[/underline] to refresh")
                if not choice.strip():
                    break
                if int(choice) == 0:
                    self.draw_heading("Video Fetcher")
                    self.manager._log(f"Refreshing started.")
                    parsed_feeds = self.manager.parse_feeds(self.manager.channels)
                    videos.clear()
                    with self.console.status(" " * 9 + "[b green]Fetching videos..."):
                        for i, channel_id in enumerate(self.manager.channels):
                            feed = parsed_feeds[i]
                            videos.extend(self.manager.fetch_videos(channel_id, feed))
                    if not videos:
                        self.draw_heading("Video Fetcher")
                        self.show_message("No videos found!\nCheck your subscriptions and internet connection.", "red")
                        return
                    videos.sort(key=lambda x: x["published"], reverse=True)
                    cutoff_date = datetime.now(videos[0]["published"].tzinfo) - timedelta(days=self.manager.config["days_filter"])
                    videos[:] = [v for v in videos if v["published"] > cutoff_date]
                    if not videos:
                        self.draw_heading("Video Fetcher")
                        self.show_message("No videos found!\nCheck your filters and internet connection.", "red")
                        return
                    self.manager._log(f"[b green]Refreshed successfully.")
                    continue
                if choice.isdigit() and 1 <= int(choice) <= len(videos):
                    video = videos[int(choice) - 1]
                    video_details = {
                        'title': video["title"],
                        'id': video["id"],
                        'author': video.get("author", "Unknown Channel"),
                        'watched_at': datetime.now().isoformat(),
                        'duration': duration
                    }
                    if video_details:
                        self.manager.watched.add(tuple(video_details.items()))
                        self.manager.save_watched()
                    self.manager.open_video_instance(video["link"])
        else:
            self.draw_heading("Video Fetcher")
            self.show_message("Please add at least one channel first!", "yellow")

    def add_channel(self) -> None:
        """Add a YouTube channel to the manager."""
        if self.manager.config.get('api_key'):
            self.draw_heading("Add New Channel")
            answer = Prompt.ask("\n" + " " * 9 + f"Enter the YouTube channel [underline]link[/underline] or [underline]handle[/underline]")
            if answer.strip():
                try:
                    channel_id = self.manager.channel_extractor.get_channel_id(answer)
                    if channel_id not in self.manager.channels:
                        self.manager.channels.append(channel_id)
                        self.manager.save_channels()
                        self.channel_map = self.manager.channel_extractor.get_channel_names(self.channel_ids)
                        self.draw_heading("Add New Channel")
                        self.show_message("New channel added!", "green")
                    else:
                        self.draw_heading("Add New Channel")
                        self.show_message("Channel already exists.", "yellow")
                except Exception as e:
                    self.draw_heading("Add New Channel")
                    self.show_message(f"Error: {str(e)}", "red")
        else:
            self.draw_heading("Add New Channel")
            self.show_message("Please set YouTube API key in settings first!", "yellow")
            
    def list_channels(self) -> None:
        """List all managed YouTube channels."""
        if self.manager.channels:
            self.draw_heading("Channel List")
            table = Table(box=box.ROUNDED, header_style="bold magenta")
            for _ in range(0, 2):
                table.add_column("[white]#", justify="center")
                table.add_column("Channel", justify="center", style="b white")
                table.add_column("YouTube ID", justify="center", style="dim italic")
            num_channels = len(self.channel_ids)
            for i in range(0, num_channels, 2):
                row_data = []
                for j in range(2):
                    if i + j < num_channels:
                        idx = i+j +1
                        channel_id = self.channel_ids[i+j]
                        channel_name = self.channel_map.get(channel_id, "Unknown")
                        row_data.extend([str(idx), channel_name, channel_id])
                    else:
                        row_data.extend(["", "", ""])
                table.add_row(*row_data)
            self.console.print(Align.center(table, vertical="middle"))
            choice = Prompt.ask("\n" + " " * 9 + "Select channel [underline]index[/underline] to see info")
            if choice.isdigit() and 1 <= int(choice) <= len(self.manager.channels):
                channel_index = int(choice) - 1
                channel_id = self.manager.channels[channel_index]
                channel_info = self.manager.channel_extractor.get_channel_info(channel_id)
                if channel_info:
                    self.draw_heading("Channel Info")
                    self.show_message(f"[b yellow]Channel Name:[/b yellow] {channel_info['title']}\n[b yellow]Description:[/b yellow] {channel_info['description']}\n[b yellow]Subscribers:[/b yellow] {channel_info['subscribers']}\n[b yellow]Total videos:[/b yellow] {channel_info['total_videos']}\n[b yellow]URL:[/b yellow] {channel_info['url']}", "white")
                elif choice:
                    self.draw_heading("Channel List")
                    self.show_message("Invalid input.", "red")
        else:
            self.draw_heading("Channel List")
            self.show_message("No channels added yet!", "yellow")

    def remove_channels(self) -> None:
        """Remove one YouTube channels from the manager."""
        if self.manager.channels:
            self.draw_heading("Remove Channel")
            table = Table(box=box.ROUNDED, header_style="bold magenta")
            for _ in range(0, 2):
                table.add_column("[white]#", justify="center", style="b red")
                table.add_column("Channel", justify="center", style="b white")
                table.add_column("YouTube ID", justify="center", style="dim italic")
            num_channels = len(self.channel_ids)
            for i in range(0, num_channels, 2):
                row_data = []
                for j in range(2):
                    if i + j < num_channels:
                        idx = i+j +1
                        channel_id = self.channel_ids[i+j]
                        channel_name = self.channel_map.get(channel_id, "Unknown")
                        row_data.extend([str(idx), channel_name, channel_id])
                    else:
                        row_data.extend(["", "", ""])
                table.add_row(*row_data)
            self.console.print(Align.center(table, vertical="middle"))
            choice = Prompt.ask("\n" + " " * 9 + "Select channel [underline]index[/underline] to remove[red]")
            self.draw_heading("Remove Channel")
            if choice.isdigit() and 1 <= int(choice) <= len(self.manager.channels):
                self.manager.channels.pop(int(choice) - 1)
                self.manager.save_channels()
                self.show_message("Channel removed!", "green")
            elif choice:
                self.show_message("Invalid input.", "red")
        else:
            self.draw_heading("Remove Channel")
            self.show_message("No channels to remove!", "yellow")

    def days_filter(self) -> None:
        """Manage the filter for the number of days."""
        self.draw_heading("Set Day Filter")
        answer = Prompt.ask("\n" + " " * 9 + f"Enter the [underline]number[/underline] of days [cyan](currently {self.manager.config['days_filter']} days)[/cyan]")
        days = ''.join([char for char in answer if char.isdigit()])
        self.draw_heading("Set Day Filter")
        if days.isdigit() and int(days) > 0:
            self.manager.config["days_filter"] = int(days)
            self.manager.save_config()
            self.show_message("Settings updated!", "green")
        elif days.strip():
            self.show_message("Invalid input", "red")
            
    def length_filter(self) -> None:
        """Manage the minimum video length filter."""
        self.draw_heading("Set Length Filter")
        answer = Prompt.ask("\n" + " " * 9 + f"Enter the [underline]number[/underline] of minutes [cyan](currently {self.manager.config['min_video_length']} minutes)[/cyan]")
        new_length = ''.join([char for char in answer if char.isdigit()])
        self.draw_heading("Set Length Filter")
        if new_length.isdigit() and int(new_length) > 0:
            self.manager.config["min_video_length"] = int(new_length)
            self.manager.save_config()
            self.show_message("Settings updated!", "green")
        elif new_length.strip():
            self.show_message("Invalid input", "red")

    def manage_api(self) -> None:
        """Manage the YouTube API key."""
        self.draw_heading("Set YouTube API Key")
        answer = Prompt.ask("\n" + " " * 9 + f"Enter the YouTube API Key [cyan](currently {'*' * 8 if self.manager.config.get('api_key') else 'Not Set'})[/cyan]")
        if answer.strip():
            api_key = max(answer.split(), key=len)
            api_key_pattern = re.compile(r"^[A-Za-z0-9_-]{39}$")
            if not api_key_pattern.match(api_key.strip()):
                self.draw_heading("Set YouTube API Key")
                self.show_message("Invalid API Key format.", "red")
                return
            try:
                self.manager.channel_extractor = Extractor(api_key.strip())
                self.manager.channel_extractor.youtube.videos().list(part="id", id="dQw4w9WgXcQ").execute() # dQw4w9WgXcQ is the Rickroll :D
                self.manager.config["api_key"] = api_key.strip()
                self.manager.save_config()
                self.draw_heading("Set YouTube API Key")
                self.show_message("API Key updated!", "green")
            except HttpError as e:
                self.draw_heading("Set YouTube API Key")
                if e.resp.status == 401:
                    self.show_message(f"Invalid API Key. Error: {e}", "red")
                else:
                    self.show_message(f"Error validating API Key: {e}", "red")
            except Exception as e:
                self.draw_heading("Set YouTube API Key")
                self.show_message(f"Error validating API Key: {e}", "red")
    
    def search_menu(self) -> None:
        """Displays the search menu, prompts the user for a search query, displays results,
        and allows the user to select a video to watch.
        """
        if self.manager.config.get('api_key'):
            self.draw_heading("Video Search")
            query = Prompt.ask("\n" + " " * 9 + f"Enter the search query")
            if query.strip():
                self.draw_heading("Search")
                results = self.manager.search_youtube_videos(query)
                if not results:
                    self.show_message("No videos matching your filters were found.", "yellow")
                    return
                table = Table(box=box.ROUNDED, header_style="bold magenta")
                table.add_column("[white]#", justify="center")
                table.add_column("Title", style="white")
                table.add_column("Channel", justify="center", style="b white")
                table.add_column("Duration", justify="right", style="b white")
                table.add_column("Published", justify="right", style="italic white")
                for idx, video in enumerate(results[:15]):
                    title = self.format_title(video["title"])
                    channel_name = video.get("author", "Unknown Channel")
                    duration = f"{round(video['duration'] / 60)} min"
                    published = video["published"]
                    delta = datetime.now(published.tzinfo) - published
                    time_ago = self.format_time_ago(delta)
                    table.add_row(str(idx + 1), title, channel_name, duration, time_ago)
                self.console.print(Align.center(table, vertical="middle"))
                choice = Prompt.ask("\n" + " " * 9 + "Select video [underline]index[/underline] to watch")
                if choice.isdigit() and 1 <= int(choice) <= len(results):
                    video = results[int(choice) - 1]
                    video_details = {
                        'title': video["title"],
                        'id': video["id"],
                        'author': video.get("author", "Unknown Channel"),
                        'watched_at': datetime.now().isoformat(),
                        'duration': duration
                    }
                    if video_details:
                        self.manager.watched.add(tuple(video_details.items()))
                        self.manager.save_watched()
                    self.manager.open_video_instance(f"https://www.youtube.com/watch?v={video["id"]}")
        else:
            self.draw_heading("Video Search")
            self.show_message("Please set YouTube API key in settings first!", "red")

    def watched_history(self) -> None:
        """Displays browsing history"""
        self.draw_heading("Watch History")
        watched_videos = [dict(item) for item in self.manager.watched]
        watched_videos = sorted(watched_videos, key=lambda x: x['watched_at'], reverse=True)
        if not watched_videos:
            self.show_message("No videos watched yet.", "yellow")
            return
        table = Table(box=box.ROUNDED, header_style="bold magenta")
        table.add_column("[white]#", justify="center")
        table.add_column("Title", style="white")
        table.add_column("Channel", justify="center", style="b white")
        table.add_column("Duration", justify="right", style="b white")
        table.add_column("Watched", justify="right", style="white")     
        for idx, video in enumerate(watched_videos[:15]):
            title = self.format_title(video["title"])
            channel_name = video.get("author", "Unknown Channel")
            watched_at = video.get('watched_at')
            time_ago = ""
            if watched_at:
                watched_at = datetime.fromisoformat(watched_at)
                delta = datetime.now() - watched_at
                time_ago = self.format_time_ago(delta)
            duration = video.get('duration')
            table.add_row(str(idx + 1), title, channel_name, duration, time_ago)
        self.console.print(Align.center(table, vertical="middle"))
        choice = Prompt.ask("\n" + " " * 9 + "Select video [underline]index[/underline] to rewatch")
        if choice.isdigit() and 1 <= int(choice) <= len(watched_videos):
            video = watched_videos[int(choice) - 1]
            self.manager.open_video_instance(f"https://www.youtube.com/watch?v={video['id']}")
