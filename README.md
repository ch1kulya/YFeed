## YFeed
is a cli python application that fetches recent video data using YouTube Data API and RSS feeds.
![332shots_so](https://github.com/user-attachments/assets/d85341a3-6b2e-4cc0-b799-5a833b825046)

### Installation

> [!WARNING]
> Ensure you have `Python`, `FFmpeg` and `mpv` installed. If you are using Windows, `Windows Terminal` is also recommended.

> [!TIP]
> To simplify the setup, you can use `run.bat` and `setup.bat` scripts for automation. Keep your YFeed installation up-to-date without losing data or binaries by running `update.bat`.

#### Step-by-Step Manual Setup:
1. Clone the repository
2. Install required libraries:
```
pip install -r requirements.txt
```
3. Run YFeed:
```
python src/main.py
```

#### Obtaining YouTube API Key
1. Visit the [**Google Cloud Console**](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the [**YouTube Data API v3**](https://console.cloud.google.com/apis/library/youtube.googleapis.com) for your project.
4. Generate an **API Key** from the [**Credentials**](https://console.cloud.google.com/apis/credentials) section.

### Data Structure
| **File**             | **Stores**                       |
|----------------------|----------------------------------|
| `settings.json`      | User-configurable settings       |
| `names.json`         | Subscribed channel names         |
| `channels.yfe`       | Subscribed channel IDs           |
| `watched.yfe`        | Watched video IDs                |
| `cache.json`         | Cached video data                |

#### Contributing is encouraged 🤗
