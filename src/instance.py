import sys
import os
from utils.player import MediaPlayer
from colorama import init

init(autoreset=True)
os.system("cls" if os.name == "nt" else "clear")

def watch_video(video_link):
    """Create a MediaPlayer instance and play the video at the provided link.

    Args:
        video_link (str): The URL of the video to watch.

    This function initializes a MediaPlayer object and calls its watch_video method
    to download and play the video specified by the video_link.
    """
    player = MediaPlayer()
    player.watch_video(video_link)


def main():
    """Main entry point for the player instance."""
    if len(sys.argv) < 2:
        print("No video link.")
        sys.exit(1)
    video_link = sys.argv[1]
    watch_video(video_link)

if __name__ == "__main__":
    main()
