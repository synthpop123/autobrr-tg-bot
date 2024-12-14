"""
Movie Release Notification Script

This script fetches movie information from TMDB API and sends formatted notifications
to a Telegram channel. It handles movie details, cast information, and various metadata
to create comprehensive movie release announcements.
"""

import os
import argparse
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import requests
from tmdbv3api import TMDb, Movie, Search
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from functools import lru_cache

load_dotenv()


@dataclass
class Config:
    """Configuration class for environment variables."""
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    TMDB_LANGUAGE: str = os.getenv("TMDB_LANGUAGE", "zh-CN")
    TMDB_DEBUG: bool = bool(os.getenv("TMDB_DEBUG", False))
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID: str = os.getenv("TELEGRAM_CHANNEL_ID", "")


class MovieClient:
    """Handle all TMDB API related operations."""
    
    def __init__(self, config: Config):
        """Initialize TMDB client with configuration."""
        self.tmdb = TMDb()
        self.tmdb.api_key = config.TMDB_API_KEY
        self.tmdb.language = config.TMDB_LANGUAGE
        self.tmdb.debug = config.TMDB_DEBUG
        self.movie = Movie()
        self.search = Search()
        
        # Set retry strategy
        self.session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.movie.session = self.session
        self.search.session = self.session

    @lru_cache(maxsize=128)
    def search_movie(self, title: str, year: Optional[str] = None) -> List[Any]:
        """Search for movies by title and optional year with caching."""
        return self.search.movies(title, year=year) if year else self.search.movies(title)

    @lru_cache(maxsize=128)
    def get_movie_details(self, tmdb_id: int, language: str = None) -> Any:
        """Get detailed information for a specific movie with caching."""
        if language:
            temp_lang = self.tmdb.language
            self.tmdb.language = language
            details = self.movie.details(tmdb_id, append_to_response="credits,images")
            self.tmdb.language = temp_lang
            return details
        return self.movie.details(tmdb_id, append_to_response="credits,images")

    def get_movie_data(self, tmdb_id: int) -> tuple:
        """Get all movie data in a single request."""
        details = self.get_movie_details(tmdb_id)
        credits = details.credits
        return details, credits.cast, credits.crew

    def get_english_details(self, tmdb_id: int) -> Any:
        """Get English version of movie details."""
        return self.get_movie_details(tmdb_id, language="en_US")


class MessageFormatter:
    """Handle message formatting and organization."""

    @staticmethod
    def escape_special_chars(text: str) -> str:
        """Escape special characters for Telegram MarkdownV2 format."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text

    @staticmethod
    def format_cast(cast: List[Any], max_count: int = 3) -> str:
        """Format cast list with specified maximum number of names."""
        cast_list = []
        count = 0
        for person in cast:
            if count >= max_count:
                break
            cast_list.append(person.name)
            count += 1
        return ", ".join(cast_list)

    @staticmethod
    def format_director(crew: List[Any], max_count: int = 3) -> str:
        """Format director list with specified maximum number of names."""
        directors = []
        count = 0
        for person in crew:
            if count >= max_count:
                break
            if person.job == "Director":
                directors.append(person.name)
                count += 1
        return ", ".join(directors)

    @staticmethod
    def format_file_info(file_size: int, runtime: int) -> tuple:
        """Format file size, duration and bitrate information."""
        size_gib = f"{file_size / (1024 ** 3):.2f} GiB"
        duration = f"{runtime} 分钟"
        bitrate = f"{(file_size * 8) / (runtime * 60) / 1_000_000:.2f} Mbps"
        return size_gib, duration, bitrate

    def create_message(self, movie_data: Dict[str, Any], language: str) -> str:
        """Create formatted message for Telegram notification."""
        parts = []
        
        # Header
        parts.append(f"\\#{movie_data['indexer']} \\#{movie_data['group']}\n")
        
        # Main content
        if language == "zh-CN":
            template = [
                ("*名称*：", f"{movie_data['title']} \\({movie_data['year']}\\)"),
                ("*导演*：", self.escape_special_chars(movie_data['director'])),
                ("*演员*：", self.escape_special_chars(movie_data['starring'])),
                ("*类型*：", ", ".join(movie_data['genres'])),
                ("*标题*：", f"__{self.escape_special_chars(movie_data['torrent_name'])}__"),
                ("*信息*：", f"{self.escape_special_chars(movie_data['size'])} / "
                        f"{self.escape_special_chars(movie_data['duration'])} / "
                        f"{self.escape_special_chars(movie_data['bitrate'])}[​​​​​​​​​​​]({movie_data['poster_url']})"),
                ("\n", f"> {self.escape_special_chars(movie_data['overview'])}")
            ]
        else:
            # English template implementation here...
            pass
        
        # Merge template
        parts.extend(f"{label}{content}" for label, content in template)
        
        return "\n".join(parts)


class TelegramNotifier:
    """Handle Telegram notification sending."""

    def __init__(self, token: str, channel_id: str):
        self.token = token
        self.channel_id = channel_id
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"

    def send(self, message: str, urls: Dict[str, str]) -> None:
        """Send formatted message to Telegram channel."""
        params = {
            "chat_id": self.channel_id,
            "text": message,
            "parse_mode": "MarkdownV2",
            "link_preview_options": json.dumps({
                "enabled": True,
                "show_above_text": True
            }),
            "reply_markup": json.dumps({
                "inline_keyboard": [[
                    {"text": site, "url": url}
                    for site, url in urls.items() if url
                ]]
            })
        }
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Movie release notification script")
    parser.add_argument("--torrent_name", required=True)
    parser.add_argument("--indexer_name", required=True)
    parser.add_argument("--group_name", required=True)
    parser.add_argument("--release_year", required=True)
    parser.add_argument("--parsed_title", required=True)
    parser.add_argument("--file_size", type=int, required=True)
    args = parser.parse_args()

    config = Config()
    movie_client = MovieClient(config)
    formatter = MessageFormatter()
    notifier = TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHANNEL_ID)

    # Fetch movie information
    results = movie_client.search_movie(args.parsed_title, args.release_year)
    if not results:
        raise ValueError("No movie found with the provided title and year")

    tmdb_id = results[0].id
    details, cast, crew = movie_client.get_movie_data(tmdb_id)
    details_en = movie_client.get_english_details(tmdb_id)
    
    # Prepare movie data
    size, duration, bitrate = formatter.format_file_info(args.file_size, details.runtime)
    movie_data = {
        'title': details.title,
        'year': details.release_date.split("-")[0],
        'overview': details.overview or details_en.overview,
        'genres': [genre.name for genre in details.genres],
        'director': formatter.format_director(crew),
        'starring': formatter.format_cast(cast),
        'size': size,
        'duration': duration,
        'bitrate': bitrate,
        'indexer': args.indexer_name,
        'group': args.group_name,
        'torrent_name': args.torrent_name,
        'poster_url': f"https://image.tmdb.org/t/p/original{details_en.backdrop_path or details_en.poster_path}"
    }

    # Create and send message
    message = formatter.create_message(movie_data, config.TMDB_LANGUAGE)
    urls = {
        "TMDB": f"https://www.themoviedb.org/movie/{tmdb_id}",
        "IMDB": f"https://www.imdb.com/title/{details.imdb_id}",
        "Letterboxd": f"https://letterboxd.com/imdb/{details.imdb_id}/?adult",
        "Douban": f"https://search.douban.com/movie/subject_search?search_text={details.imdb_id}"
    }
    
    notifier.send(message, urls)


if __name__ == "__main__":
    main()
