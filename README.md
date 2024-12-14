# Movie Release Notifier for Autobrr

A Python script that sends formatted movie release notifications to Telegram channels when triggered by Autobrr filters. It fetches comprehensive movie information from TMDB API, including movie details, cast information, and metadata.

## Demo

![image](https://img.lkwplus.com/alYNMCdAShg6aXub.jpg)

## Features

- Fetches detailed movie information from TMDB API
- Supports both Chinese and English movie information
- Sends formatted notifications to Telegram channels
- Includes movie metadata, cast, director, and overview
- Provides direct links to TMDB, IMDB, Letterboxd, and Douban
- Automatic retry mechanism for API requests
- Caching for improved performance

## Installation

### Prerequisites

- Python 3.6+
- Autobrr
- TMDB API Key
- Telegram Bot Token and Channel ID

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/movie-release-notifier.git
cd movie-release-notifier
```

2. Install dependencies:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

3. Configure environment variables:

Create a `.env` file based on `.env.example`:
```bash
TMDB_API_KEY=your_tmdb_api_key
TMDB_LANGUAGE=zh-CN        # Default language for movie information
TMDB_DEBUG=False          # Enable/disable debug mode
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_telegram_channel_id
```

## Usage

### Autobrr Configuration

Add the following command to your Autobrr filter's Exec section:

```bash
/path/to/autobrr/scripts/notify.sh "{{.TorrentName}}" "{{.IndexerName}}" "{{.Group}}" "{{.Year}}" "{{.Title}}" "{{.FileSize}}"
```

### Notification Format

The script sends formatted notifications including:
- Movie title and release year
- Director and main cast
- Genre information
- Release details (file size, duration, bitrate)
- Movie overview
- Links to movie databases (TMDB, IMDB, Letterboxd, Douban)
