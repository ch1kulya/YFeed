from colorama import Fore, init
from utils.interface import Interface
from utils.manager import YouTubeFeedManager
import shutil
import sys

init(autoreset=True)

def check_dependencies():
    for dependency in ["ffmpeg", "mpv"]:
        if not shutil.which(dependency):
            print(f"Error: {dependency} is not installed or not in PATH.")
            sys.exit(1)

def main():
    """Main entry point for the YFeed application.

    This function initializes the YouTubeFeedManager and Interface, displays a greeting,
    and enters the main application loop where it responds to user input to navigate
    through the application's menus.
    """
    check_dependencies()
    manager = YouTubeFeedManager()
    interface = Interface(manager)
    interface.greet()

    while True:
        choice = interface.main_menu()
        if choice == "1":
            interface.videos_menu()
        elif choice == "2":
            interface.search_menu()
        elif choice == "3":
            interface.live_menu()
        elif choice in ["4", "5", "6"]:
            interface.channels_menu(choice)
        elif choice in ["7", "8", "9"]:
            interface.settings_menu(choice)
        elif choice == "q":
            interface.shut_down()
            break
        elif choice:
            interface.show_message("Invalid choice!", Fore.RED)

if __name__ == "__main__":
    main()
