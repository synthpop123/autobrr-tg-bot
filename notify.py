import os
import argparse
import json
import requests
from tmdbv3api import TMDb, Movie, Search

from dotenv import load_dotenv

load_dotenv()


class ENV:
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    TMDB_LANGUAGE = os.getenv("TMDB_LANGUAGE") if os.getenv("TMDB_LANGUAGE") else "zh-CN"
    TMDB_DEBUG = os.getenv("TMDB_DEBUG") if os.getenv("TMDB_DEBUG") else False
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")


class RELEASE:
    def __init__(self, env):
        self.tmdb = TMDb()
        self.tmdb.api_key = env.TMDB_API_KEY
        self.tmdb.language = env.TMDB_LANGUAGE
        self.tmdb.debug = env.TMDB_DEBUG
        self.genre_list = []

    def search_movie(self, title, year=None):
        search = Search()
        if year:
            return search.movies(title, year=year)
        else:
            return search.movies(title)

    def get_movie_details(self, tmdb_id):
        movie = Movie()
        return movie.details(tmdb_id)

    def get_movie_cast(self, tmdb_id):
        movie = Movie()
        return movie.credits(tmdb_id).cast

    def get_movie_crew(self, tmdb_id):
        movie = Movie()
        return movie.credits(tmdb_id).crew

    def get_fallback_en_overview(self, tmdb_id):
        movie = Movie()
        return movie.translations(tmdb_id).en.overview


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--torrent_name", type=str, required=True)
    parser.add_argument("--indexer_name", type=str, required=True)
    parser.add_argument("--group_name", type=str, required=True)
    parser.add_argument("--release_year", type=str, required=True)
    parser.add_argument("--parsed_title", type=str, required=True)
    parser.add_argument("--file_size", type=str, required=True)

    return parser.parse_args()


def convert_bytes_to_gib(bytes):
    return f"{bytes / (1024 * 1024 * 1024):.2f} GiB"


def calculate_bitrate(file_size, duration):
    # file_size is in bytes
    # duration is in minutes
    # Convert file size from bytes to bits (1 byte = 8 bits)
    file_size_bits = file_size * 8
    
    # Convert duration from minutes to seconds (1 minute = 60 seconds)
    duration_seconds = duration * 60
    
    # Calculate bitrate in bits per second (bps)
    bitrate_bps = file_size_bits / duration_seconds
    
    # Convert bitrate to megabits per second (Mbps)
    bitrate_Mbps = bitrate_bps / 1_000_000
    
    # Return the bitrate formatted to two decimal places
    return f"{bitrate_Mbps:.2f} Mbps"


def calculate_duration(runtime):
    # runtime is in minutes
    return f"{runtime} 分钟"


def format_message(message):
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        message = message.replace(char, f"\\{char}")
    return message


def format_starring(cast):
    starring_list = []
    max_starring_num = 3

    for index, person in enumerate(cast):
        if index >= max_starring_num:
            break
        starring_list.append(person.name)
    return ", ".join(starring_list)


def format_director(crew):
    director_list = []
    max_director_num = 3

    for person in crew:
        if person.job == "Director":
            director_list.append(person.name)
        if len(director_list) >= max_director_num:
            break
    return ", ".join(director_list)


def organize_message(language, title, year, overview=None, genre_list=None, tmdb_id=None, tmdb_url=None, torrent_name=None, indexer_name=None, group_name=None, file_size=None, bitrate=None, duration=None, starring=None, director=None, poster_url=None):
    content_parts = []
    
    if language == "zh-CN":
        content_parts.append(f"\\#{indexer_name} \\#{group_name}\n")
        
        if title and year:
            content_parts.append(f"*名称*：`{title}` \\({year}\\)")
        if director:
            content_parts.append(f"*导演*：{format_message(director)}")
        if starring:
            content_parts.append(f"*演员*：{format_message(starring)}")
        if genre_list:
            genres = ", ".join(genre_list)
            content_parts.append(f"*类型*：{genres}")
        if torrent_name:
            content_parts.append(f"*标题*：`{format_message(torrent_name)}`")
        if file_size:
            content_parts.append(f"*信息*：{format_message(file_size)} / {format_message(duration)} / {format_message(bitrate)}[​​​​​​​​​​​]({poster_url})")
        if overview:
            content_parts.append(f"*简介*：\n> {format_message(overview)}")
    else:
        content_parts.append(f"\\#{indexer_name} \\#{group_name}\n")
        
        if title and year:
            content_parts.append(f"*Movie Name*：`{title}` \\({year}\\)")
        if director:
            content_parts.append(f"*Director*：{format_message(director)}")
        if starring:
            content_parts.append(f"*Starring*：{format_message(starring)}")
        if genre_list:
            genres = ", ".join(genre_list)
            content_parts.append(f"*Genres*：{genres}")
        if torrent_name:
            content_parts.append(f"*Torrent Name*：`{format_message(torrent_name)}`")
        if file_size:
            content_parts.append(f"*Info*：{format_message(file_size)}")
        if tmdb_id and tmdb_url:
            content_parts.append(f"*TMDB ID*：[{tmdb_id}]({tmdb_url})")
        if overview:
            content_parts.append(f"*Overview*：\n> {format_message(overview)}")

    return "\n".join(content_parts)


def send_message(message, bot_token, channel_id, tmdb_url=None, imdb_url=None, letterboxd_url=None, douban_url=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "link_preview_options": json.dumps({
            "enabled": True,
            "show_above_text": True
        }),
        "reply_markup": json.dumps({
            "inline_keyboard": [
                [{"text": "TMDB", "url": tmdb_url}, {"text": "IMDB", "url": imdb_url}, {"text": "Letterboxd", "url": letterboxd_url}, {"text": "Douban", "url": douban_url}]
            ]
        })
    }
    # print(url, params)
    response = requests.get(url, params=params)
    print(response.json())


def main():
    env = ENV()

    args = parse_args()
    title = args.parsed_title
    year = args.release_year
    file_size = convert_bytes_to_gib(int(args.file_size))

    release = RELEASE(env)

    language = release.tmdb.language
    results = release.search_movie(title, year)
    tmdb_id = results[0].id
    details = release.get_movie_details(tmdb_id)

    if not results or not details:
        overview = None
        genre_list = None
        tmdb_id = None
        tmdb_url = None
        starring = None
        director = None
        imdb_url = None
        letterboxd_url = None
        douban_url = None
        poster_url = None
        bitrate = None
        duration = None
    else:
        title = details.title
        year = details.release_date.split("-")[0]
        overview = details.overview

        genre_list = [genre.name for genre in details.genres]

        tmdb_id = details.id
        imdb_id = details.imdb_id
        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}"
        imdb_url = f"https://www.imdb.com/title/{imdb_id}"
        letterboxd_url = f"https://letterboxd.com/imdb/{imdb_id}/?adult"
        douban_url = f"https://search.douban.com/movie/subject_search?search_text={imdb_id}"

        cast = release.get_movie_cast(tmdb_id)
        crew = release.get_movie_crew(tmdb_id)
        starring = format_starring(cast)
        director = format_director(crew)

        duration = calculate_duration(details.runtime)
        bitrate = calculate_bitrate(int(args.file_size), details.runtime)

        # 切换到英文获取海报和 Fallback 简介
        relese_en = RELEASE(env)
        relese_en.tmdb.language = "en_US"
        details_en = relese_en.get_movie_details(tmdb_id)
        poster_path = details_en.backdrop_path
        if not poster_path:
            poster_path = details_en.poster_path
        poster_url = f"https://image.tmdb.org/t/p/original{poster_path}"

        if not overview:
            overview = details_en.overview

    notify_message = organize_message(
        language=language,
        title=title,
        year=year,
        overview=overview,
        genre_list=genre_list,
        tmdb_id=tmdb_id,
        tmdb_url=tmdb_url,
        torrent_name=args.torrent_name,
        indexer_name=args.indexer_name,
        group_name=args.group_name,
        file_size=file_size,
        bitrate=bitrate,
        duration=duration,
        starring=starring,
        director=director,
        poster_url=poster_url
    )

    print(f"{notify_message=}")

    send_message(notify_message, env.TELEGRAM_BOT_TOKEN, env.TELEGRAM_CHANNEL_ID, tmdb_url, imdb_url, letterboxd_url, douban_url)


if __name__ == "__main__":
    main()