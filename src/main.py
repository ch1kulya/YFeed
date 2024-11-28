import os
import pyfiglet
import datetime
from time import sleep
from colorama import Fore, init
from utils.interface import Interface
from utils.manager import YouTubeFeedManager

init(autoreset=True)

def main():
    # Main application entry point
    manager = YouTubeFeedManager()
    interface = Interface(manager)
    greeting = f"Good {['Night', 'Morning', 'Afternoon', 'Evening'][(datetime.datetime.now().hour // 6)]}!"
    greeting_art = pyfiglet.figlet_format(greeting, font='slant', width=interface.terminal_width)
    gradient_art = interface.gradient_color(
        greeting_art,
        (255, 200, 255),
        (255, 99, 255)
    )
    print("\n")
    for line in gradient_art.split('\n'):
        print(" " * 3 + line)
    print("\n")
    sleep(1.5)
    os.system("cls" if os.name == "nt" else "clear")

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
            goodbye_art = pyfiglet.figlet_format("Goodbye!", font='slant', width=interface.terminal_width)
            gradient_art = interface.gradient_color(
                goodbye_art,
                (255, 255, 255),
                (255, 69, 255)
            )
            print("\n")
            for line in gradient_art.split('\n'):
                print(" " * 3 + line)
            print("\n")
            break
        else:
            interface.show_message("Invalid choice!", Fore.RED)

if __name__ == "__main__":
    main()
