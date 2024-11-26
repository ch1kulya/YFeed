import os
import pyfiglet
from colorama import Fore, init
from utils.interface import Interface
from utils.manager import YouTubeFeedManager

init(autoreset=True)

def main():
    # Main application entry point
    manager = YouTubeFeedManager()
    interface = Interface(manager)

    while True:
        choice = interface.main_menu()
        if choice == "1":
            interface.videos_menu()
        elif choice == "2":
            interface.channels_menu()
        elif choice == "3":
            interface.settings_menu()
        elif choice == "4":
            os.system("cls" if os.name == "nt" else "clear")
            logo = pyfiglet.figlet_format("Goodbye!", font='slant', width=interface.terminal_width)
            gradient_logo = interface.gradient_color(
                logo,
                (255, 255, 255),
                (255, 69, 255)
            )
            print("\n")
            for line in gradient_logo.split('\n'):
                print(" " * 3 + line)
            print("\n")
            break
        else:
            interface.show_message("Invalid choice!", Fore.RED)

if __name__ == "__main__":
    main()
