import sys
import os
from utils.player import MediaPlayer
from colorama import init

init(autoreset=True)
os.system("cls" if os.name == "nt" else "clear")

def watch_video(video_link):
    player = MediaPlayer()
    player.watch_video(video_link)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("No video link.")
        sys.exit(1)

    video_link = sys.argv[1]
    watch_video(video_link)
