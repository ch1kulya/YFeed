import os
import sys
import vlc
import string
import random
import webbrowser
import pyfiglet
import subprocess
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
        self.process = None
        
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

        temp_file = 'video-' + ''.join(random.choices(string.ascii_letters, k=8)) + '.webm' # Temporary file

        # yt-dlp options for downloading the best video+audio quality
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'merge_output_format': 'webm',
            'outtmpl': temp_file,
            'progress_hooks': [self.download_progress_hook],
            'quiet': True,
            'no_warnings': True,
            'logger': QuietLogger(),
            'max_downloads': 8,
            'concurrent_fragments': 8,
            'nooverwrites': False,
        }

        try:
            # Download the video
            with YoutubeDL(ydl_opts) as ydl:
                print("Downloading video...")
                ydl.download([url])
            
            # Play the video using python-vlc
            print(f"Playing {temp_file}...")
            self.play_video(temp_file)
            
        except Exception as e:
            print(Fore.RED + f"An error occurred: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(Style.DIM + "Temporary file removed.")
            print(Style.DIM + "Playing in browser.")
            sleep(1)
            webbrowser.open(url)
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(Style.DIM + "Temporary file removed.")
            sleep(1)
                
    def play_video(self, video_file):
        # Start mpv with flags
        command = f"mpv --hwdec=auto --hr-seek=always --ontop --autofit=50% --volume=50 --cache=no --no-border --log-file=mpv_log.txt --window-corners=round --osc=no {video_file}"

        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"{Fore.RED}Error starting mpv process: {e}")
            return

        # MPV controls information
        print(f"\n{Fore.YELLOW}Video Controls{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Use the following {Fore.CYAN}binds{Fore.WHITE} to control the video:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}1.{Fore.WHITE} Left double click{Fore.LIGHTBLACK_EX} — Toggle fullscreen on/off")
        print(f"{Fore.CYAN}2.{Fore.WHITE} Right click{Fore.LIGHTBLACK_EX} — Toggle pause on/off")
        print(f"{Fore.CYAN}3.{Fore.WHITE} Wheel up/down{Fore.LIGHTBLACK_EX} — Decrease/increase volume")
        print(f"{Fore.CYAN}4.{Fore.WHITE} Ctrl+Wheel up/down{Fore.LIGHTBLACK_EX} — Change video zoom")
        print(f"{Fore.CYAN}5.{Fore.WHITE} Left/Right Arrow{Fore.LIGHTBLACK_EX} — Rewind/Fast forward{Style.RESET_ALL}")

        # Wait for the mpv process to finish
        process.wait()

        print(f"{Fore.CYAN}MPV player closed. Exiting video player...\n")
        sleep(1)
