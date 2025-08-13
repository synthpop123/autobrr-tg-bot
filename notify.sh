#! /bin/bash

# Acquire the current directory of the script
SCRIPT_DIR=$(dirname "$0")
LOG_FILE="$SCRIPT_DIR/notify.log"

# Create log function
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

cd "$SCRIPT_DIR"
source .venv/bin/activate

# Log script start
log_message "----------------------------------------"
log_message "Script started"

# Required parameters check
if [ $# -lt 6 ] || [ $# -gt 7 ]; then
    log_message "Error: Invalid number of parameters"
    echo "Usage: $0 <torrent_name> <indexer_name> <group_name> <release_year> <parsed_title> <file_size> [meta_imdb]"
    exit 1
fi

torrent_name=$1
indexer_name=$2
group_name=$3
release_year=$4 
parsed_title=$5
file_size=$6
meta_imdb=$7

# Log received parameters
log_message "Parameters received:"
log_message "Torrent: $torrent_name"
log_message "Indexer: $indexer_name"
log_message "Group: $group_name"
log_message "Year: $release_year"
log_message "Title: $parsed_title"
log_message "Size: $file_size"
if [ -n "$meta_imdb" ]; then
    log_message "Meta IMDB: $meta_imdb"
fi

# Run notify.py
if [ -n "$meta_imdb" ]; then
    # Run with meta_imdb parameter
    if python3 notify.py --torrent_name "$torrent_name" --indexer_name "$indexer_name" --group_name "$group_name" --release_year "$release_year" --parsed_title "$parsed_title" --file_size "$file_size" --meta_imdb "$meta_imdb"; then
        log_message "Python script executed successfully with IMDB ID"
    else
        log_message "Error: Python script execution failed with IMDB ID"
    fi
else
    # Run without meta_imdb parameter
    if python3 notify.py --torrent_name "$torrent_name" --indexer_name "$indexer_name" --group_name "$group_name" --release_year "$release_year" --parsed_title "$parsed_title" --file_size "$file_size"; then
        log_message "Python script executed successfully"
    else
        log_message "Error: Python script execution failed"
    fi
fi

# Log script end
log_message "Script finished"
log_message "----------------------------------------"

deactivate
