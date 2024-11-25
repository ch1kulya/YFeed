## YFeed
is a cli python application that fetches recent video data using YouTube Data API and RSS feeds.
![screenshot](https://github.com/user-attachments/assets/9959285b-6932-4480-aa5e-cfbc3c58c3db)

### Installation

#### I. Setup
1. Clone the repository
2. Ensure you have Python, VLC and ffmpeg installed, and then install the required libraries:
```
pip install -r requirements.txt
```
3. Run Yfeed:
```
python src/main.py
```
> [!TIP]
> You can use `run.bat` and `update.bat` to automate this process.

#### II. Obtain YouTube API Key
1. Visit the [**Google Cloud Console**](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the [**YouTube Data API v3**](https://console.cloud.google.com/apis/library/youtube.googleapis.com) for your project.
4. Generate an **API Key** from the [**Credentials**](https://console.cloud.google.com/apis/credentials) section.

### Data Structure
- **`data/settings.json`**: Stores user-configurable settings.
- **`data/channels.yfe`**: Stores subscribed channel IDs.
- **`data/watched.yfe`**: Stores watched video IDs.

#### Contributing is encouraged 🤗
