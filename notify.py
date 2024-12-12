import os
import argparse
import json
import requests
from tmdbv3api import TMDb, Movie

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

    def search_movie(self, title):
        movie = Movie()
        return movie.search(title)

    def get_movie_details(self, tmdb_id):
        movie = Movie()
        return movie.details(tmdb_id)

    def get_movie_cast(self, tmdb_id):
        movie = Movie()
        return movie.credits(tmdb_id).cast

    def get_movie_crew(self, tmdb_id):
        movie = Movie()
        return movie.credits(tmdb_id).crew

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--torrent_name", type=str, required=True)
    parser.add_argument("--indexer_name", type=str, required=True)
    parser.add_argument("--group_name", type=str, required=True)
    parser.add_argument("--release_year", type=str, required=True)
    parser.add_argument("--parsed_title", type=str, required=True)
    parser.add_argument("--file_size", type=str, required=True)

    return parser.parse_args()


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


def organize_message(language, title, year, overview=None, genre_list=None, tmdb_id=None, tmdb_url=None, torrent_name=None, indexer_name=None, group_name=None, file_size=None, starring=None, director=None):    
    genres = ", ".join(genre_list)
    if language == "zh-CN":
        content = f"""\\#{indexer_name}

*电影名称*：{title} \\({year}\\)
*导演*：{format_message(director)}
*演员*：{format_message(starring)}
*类型*：{genres}
*资源名称*：__{format_message(torrent_name)}__
*组名*：{group_name}
*文件大小*：{format_message(file_size)}
*TMDB ID*：[{tmdb_id}]({tmdb_url})
*剧情简介*：
> {format_message(overview)}
"""
    else:
        content = f"""\\#{indexer_name}
        
*Movie Name*：{title} \\({year}\\)
*Director*：{format_message(director)}
*Starring*：{format_message(starring)}
*Genres*：{genres}
*Torrent Name*：__{format_message(torrent_name)}__
*Group Name*：{group_name}
*File Size*：{format_message(file_size)}
*TMDB ID*：[{tmdb_id}]({tmdb_url})
*Overview*：
> {format_message(overview)}
"""
    return content


def send_message(message, bot_token, channel_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": channel_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "link_preview_options": json.dumps({
            "enabled": True,
            "show_above_text": True
        })
    }
    print(url, params)
    response = requests.get(url, params=params)
    print(response.json())


def main():
    env = ENV()

    args = parse_args()

    release = RELEASE(env)
    
    results = release.search_movie(args.parsed_title)
    tmdb_id = results[0].id
    details = release.get_movie_details(tmdb_id)

    if not results or not details:
        title = args.parsed_title
        year = args.release_year
        overview = None
        genre_list = None
        tmdb_id = None
        tmdb_url = None
        starring = None
        director = None
    else:
        title = details.title
        year = details.release_date.split("-")[0]
        overview = details.overview

        genre_list = [genre.name for genre in details.genres]

        tmdb_id = details.id
        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}"

        cast = release.get_movie_cast(tmdb_id)
        crew = release.get_movie_crew(tmdb_id)
        starring = format_starring(cast)
        director = format_director(crew)

    notify_message = organize_message(
        language=release.tmdb.language,
        title=title,
        year=year,
        overview=overview,
        genre_list=genre_list,
        tmdb_id=tmdb_id,
        tmdb_url=tmdb_url,
        torrent_name=args.torrent_name,
        indexer_name=args.indexer_name,
        group_name=args.group_name,
        file_size=args.file_size,
        starring=starring,
        director=director
    )

    send_message(notify_message, env.TELEGRAM_BOT_TOKEN, env.TELEGRAM_CHANNEL_ID)


if __name__ == "__main__":
    main()