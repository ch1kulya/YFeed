import os
import sys
import vlc
import string
import random
import webbrowser
import pyfiglet
from tqdm import tqdm
from time import sleep
from yt_dlp import YoutubeDL
from colorama import Fore, Style, Cursor
from utils.interface import Interface
from utils.manager import YouTubeFeedManager

class QuietLogger:
    def debug(self, msg):
        pass
    def info(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

class MediaPlayer:
    def __init__(self):
        self.progress_bar = None
        
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
        manager = YouTubeFeedManager()
        interface = Interface(manager)
        logo = pyfiglet.figlet_format("YFeed Media Player", font='slant', width=interface.terminal_width)
        gradient_logo = interface.gradient_color(
            logo,
            (255, 51, 51),
            (255, 69, 255)
        )
        print("\n")
        for line in gradient_logo.split('\n'):
            print(" " * 3 + line)
        print("\n")

        temp_file = 'video-' + ''.join(random.choices(string.ascii_letters, k=8)) # Temporary file

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
            # Download the video
            with YoutubeDL(ydl_opts) as ydl:
                print("Downloading video...")
                ydl.download([url])
            
            # Play the video using python-vlc
            print(f"Playing {temp_file}.webm...")
            self.play_video(temp_file + ".webm")
            
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
            if os.path.exists(temp_file + ".webm"):
                os.remove(temp_file + ".webm")
                print(Style.DIM + "Temporary file removed.")
            print(Style.DIM + "Playing in browser.")
            sleep(5)
            webbrowser.open(url)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file + ".webm"):
                os.remove(temp_file + ".webm")
                print(Style.DIM + "Temporary file removed.")
            sleep(1)
                
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
