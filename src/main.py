from utils.interface import Interface
from utils.manager import FeedManager
import shutil
import sys

def check_dependencies():
    """Checks if required binaries are installed and available in the system's PATH.

    If any dependency is missing, the program exits with an error message.
    """
    missing_dependencies = False
    for dependency in ["ffmpeg", "mpv"]:
        if not shutil.which(dependency):
            print(f"Missing dependencies: {dependency} is not installed or not in PATH.")
            missing_dependencies = True
    if missing_dependencies:
            sys.exit(1)

def main():
    """Main entry point for the YFeed application.

    This function initializes the FeedManager and Interface, displays a greeting,
    and enters the main application loop where it responds to user input to navigate
    through the application's menus.
    """
    check_dependencies()
    manager = FeedManager()
    interface = Interface(manager)
    interface.greet()
    actions = {
        "1": interface.videos_menu,
        "2": interface.search_menu,
        "3": interface.watched_history,
        "4": interface.add_channel,
        "5": interface.list_channels,
        "6": interface.remove_channels,
        "7": interface.days_filter,
        "8": interface.length_filter,
        "9": interface.manage_api,
        "q": interface.shut_down
    }
    while True:
        choice = interface.main_menu()
        action = actions.get(choice)
        if action:
            action()
            if choice == "q":
                break
        elif choice:
            interface.show_message("Invalid choice!", "red")

if __name__ == "__main__":
    main()
