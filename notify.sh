#! /bin/bash

# Acquire the current directory of the script
SCRIPT_DIR=$(dirname "$0")

cd "$SCRIPT_DIR"
source .venv/bin/activate

# Required parameters:
# 1. Torrent name: {{.TorrentName}}
# 2. Indexer name: {{.IndexerName}}
# 3. Group name: {{.Group}}
# 4. Release year: {{.Year}}
# 5. Parsed title: {{.Title}}
# 6. File size: {{.FileSize}}
if [ $# -ne 6 ]; then
    echo "Usage: $0 <bot_token> <channel_id> <torrent_name> <indexer_name> <group_name> <release_year> <parsed_title> <file_size>"
    exit 1
fi

torrent_name=$1
indexer_name=$2
group_name=$3
release_year=$4 
parsed_title=$5
file_size=$6

python3 notify.py --torrent_name "$torrent_name" --indexer_name "$indexer_name" --group_name "$group_name" --release_year "$release_year" --parsed_title "$parsed_title" --file_size "$file_size"

echo "--------------------------------"
echo "Current time: $(date)"
echo "Torrent: $torrent_name"
echo "Indexer: $indexer_name"
echo "Group: $group_name"
echo "Notification sent successfully!"

deactivate
