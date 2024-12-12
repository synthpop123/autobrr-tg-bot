# Autobrr Notify

Triggered when an Autobrr filter is matched, send a notification to Telegram Channel.

## Usage

### Install dependencies

Using uv by default, and can switch to any other python package manager. Just edit `notify.sh` to use your preferred package manager.

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Add environment variables

Edit the `.env` file and add the following variables:

```bash
TMDB_API_KEY=your_tmdb_api_key
TMDB_LANGUAGE=zh-CN # Default language is zh-CN
TMDB_DEBUG=False # Default is False
PATH_TO_AUTOBRR_SCRIPTS=/path/to/autobrr/scripts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_telegram_channel_id
```

### Add this to Autobrr filter Exec section

```bash
/path/to/autobrr/scripts/notify.sh "{{.TorrentName}}" "{{.FilterName}}" "{{.Group}}" "{{.ReleaseYear}}" "{{.ParsedTitle}}" "{{.SizeString}}"
```
