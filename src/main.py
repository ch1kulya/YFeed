from colorama import Fore, init
from utils.interface import Interface
from utils.manager import YouTubeFeedManager

init(autoreset=True)

def main():
    # Main application entry point
    manager = YouTubeFeedManager()
    interface = Interface(manager)
    interface.greet()

    while True:
        choice = interface.main_menu()
        if choice == "1":
            interface.videos_menu()
        elif choice == "2":
            interface.channels_menu()
        elif choice == "3":
            interface.settings_menu()
        elif choice == "4":
            interface.shut_down()
            break
        else:
            interface.show_message("Invalid choice!", Fore.RED)

if __name__ == "__main__":
    main()
