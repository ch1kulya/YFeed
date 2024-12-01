import os
import webbrowser
import subprocess
from time import sleep
from yt_dlp import YoutubeDL
from colorama import Fore, Style
from utils.interface import Interface
from utils.manager import YouTubeFeedManager

class MediaPlayer:
    def __init__(self):
        self.manager = YouTubeFeedManager()
        self.interface = Interface(self.manager)
    
    def watch_video(self, url):
        self.interface.draw_logo("Media Loader")
        if 'v=' in url:
            temp_file = 'video-' + url.split('v=')[1][:11] + '.webm'
        elif '/' in url:
            temp_file = 'video-' + url.split('/')[-1] + '.webm'
        else:
            temp_file = 'video-invalid.webm'

        # yt-dlp options for downloading the best video+audio quality
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'merge_output_format': 'webm',
            'outtmpl': temp_file,
            'progress_hooks': [],
            'quiet': True,
            'max_downloads': 8,
            'concurrent_fragments': 8,
            'nooverwrites': False,
            'postprocessors': [{
                'key': 'SponsorBlock',
                'api': 'https://sponsor.ajay.app',
                'categories': {
                    'sponsor',
                    'intro',
                    'outro',
                    'selfpromo',
                    'filler',
                },
                'when': 'after_filter', 
            }, {
                'key': 'ModifyChapters',
                'remove_sponsor_segments': {'sponsor', 'intro', 'outro', 'selfpromo', 'filler'},
            }],
        }

        try:
            if os.path.exists(temp_file):
                print(f"Video already downloaded: {temp_file}")
            else:
                with YoutubeDL(ydl_opts) as ydl:
                    print("Downloading video...")
                    ydl.download([url])
            
            # Play the video using mpv
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
                
    def play_video(self, video_file):
        # Start mpv with flags
        command = (
            f"mpv --hwdec=auto --hr-seek=always --ontop --autofit=40% --volume=50 "
            f"--cache=yes --cache-secs=20 --no-border "
            f"--osc=no --window-corners=round {video_file}"
        )

        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
            print("Video playback started successfully.")
        except Exception as e:
            print(f"Error starting mpv: {e}")
            sleep(1)
