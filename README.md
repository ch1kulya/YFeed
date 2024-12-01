## YFeed
is a cli python application that fetches recent video data using YouTube Data API and RSS feeds.
![332shots_so](https://github.com/user-attachments/assets/d85341a3-6b2e-4cc0-b799-5a833b825046)

### Installation

> [!WARNING]
> Ensure you have **Python**, **fmmpeg** and **mpv** installed. If you are using Windows, **wt** is also recommended.

> [!TIP]
> You can use `run.bat` and `update.bat` to automate this process.

#### I. Setup
1. Clone the repository
2. Install required libraries:
```
pip install -r requirements.txt
```
1. Run YFeed:
```
python src/main.py
```

#### II. Obtain YouTube API Key
1. Visit the [**Google Cloud Console**](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the [**YouTube Data API v3**](https://console.cloud.google.com/apis/library/youtube.googleapis.com) for your project.
4. Generate an **API Key** from the [**Credentials**](https://console.cloud.google.com/apis/credentials) section.

### Data Structure
- **`data/settings.json`**: Stores user-configurable settings.
- **`data/names.json`**: Stores subscribed channel names.
- **`data/channels.yfe`**: Stores subscribed channel IDs.
- **`data/watched.yfe`**: Stores watched video IDs.
- **`data/cache.json`**: Stores cached video data.

#### Contributing is encouraged 🤗
