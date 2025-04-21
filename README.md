<div align="center">
   
## YFeed
is a cli python application that fetches recent video data using YouTube Data API and RSS feeds. 

[![CI](https://github.com/ch1kulya/YFeed/actions/workflows/ci.yml/badge.svg)](https://github.com/ch1kulya/YFeed/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ch1kulya/YFeed/branch/main/graph/badge.svg)](https://codecov.io/gh/ch1kulya/YFeed)
![332shots_so](https://github.com/user-attachments/assets/d85341a3-6b2e-4cc0-b799-5a833b825046)

</div>

### Installation

> [!WARNING]
> Make sure you have `Python 3.12` or newer, `FFmpeg` and `mpv` installed. If you are using Windows, `Windows Terminal` is also recommended. If you are using Linux you should have `venv` module. If YouTube is not available in your country then this application will not work either.

> [!TIP]
> To simplify installation and startup you can use `run` scripts for automation, choose them depending on your system.

#### Step-by-Step Manual Setup:
1. Clone the repository or download `YFeed.zip` from the latest release.
2. Install required libraries:
```
pip install -r requirements.txt
```
3. Run YFeed:
```
python src/main.py
```

#### Obtaining YouTube API Key:
1. Visit the [**Google Cloud Console**](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the [**YouTube Data API v3**](https://console.cloud.google.com/apis/library/youtube.googleapis.com) for your project.
4. Generate an **API Key** from the [**Credentials**](https://console.cloud.google.com/apis/credentials) section.

#### Contributing is encouraged 🤗
