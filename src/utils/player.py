import os
import subprocess
from time import sleep
from yt_dlp import YoutubeDL
from utils.interface import Interface
from utils.manager import FeedManager

class MediaPlayer:
    """Handles video playback functionality, including downloading and playing videos using external tools."""

    def __init__(self):
        """Initialize the MediaPlayer with a FeedManager and an Interface instance."""
        self.manager = FeedManager()
        self.interface = Interface(self.manager)
    
    def watch_video(self, url):
        """Download and play a YouTube video based on the provided URL.

        This method attempts to download the video using yt-dlp. If the video is already
        downloaded, it skips the download step. After downloading, it plays the video
        using the specified media player.

        Args:
            url (str): The URL of the YouTube video to watch.

        If downloading fails, it attempts to open the video in a web browser.
        """
        self.interface.draw_heading("Media Loader")
        if 'v=' in url:
            temp_file = 'video-' + url.split('v=')[1][:11] + '.webm'
        elif '=' in url:
            temp_file = 'video-' + url.split('=')[-1] + '.webm'
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
                self.manager._log(f"Video already downloaded: {temp_file}")
            else:
                with YoutubeDL(ydl_opts) as ydl:
                    self.manager._log("Downloading video...")
                    ydl.download([url])
            self.manager._log(f"Playing {temp_file}...")
            self.play_video(temp_file)
            
        except Exception as e:
            self.manager._log(f"An error occurred: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
                self.manager._log("Temporary file removed.")
            sleep(1)
                
    def play_video(self, video_file):
        """Play the specified video file using the mpv media player with predefined settings.

        Args:
            video_file (str): The path to the video file to be played.

        This method constructs a command with various mpv options and executes it using subprocess.
        """
        mpv_command = [
            "mpv",
            "--hwdec=auto",
            "--hr-seek=always",
            "--autofit=40%",
            "--volume=50",
            "--cache=yes",
            "--cache-secs=20",
            "--no-border",
            "--osc=no",
            "--really-quiet",
        ]
        if os.name == 'nt':
            mpv_command.append("--window-corners=round")
        elif os.name == 'posix':
            mpv_command.append("--profile=sw-fast")
        mpv_command.append(video_file)
        try:
            subprocess.Popen(
                mpv_command, stdout=None, stderr=None
            )
            self.manager._log("Video playback started successfully.")
        except FileNotFoundError:
            self.manager._log(f"Error: mpv not found, make sure it is installed on this system.")
            sleep(1)
        except Exception as e:
            self.manager._log(f"Error starting mpv: {e}")
            sleep(1)
