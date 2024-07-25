import argparse
import csv
import json
import struct
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


def retrieve_itunes_identifier(title, artist):
    headers = {
        "X-Apple-Store-Front": "143446-10,32 ab:rSwnYxS0 t:music2",
        "X-Apple-Tz": "7200",
    }
    url = (
        "https://itunes.apple.com/WebObjects/MZStore.woa/wa/search?clientApplication=MusicPlayer&term="
        + urllib.parse.quote(title)
    )
    request = urllib.request.Request(url, None, headers)

    try:
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode("utf-8"))
        songs = [
            result
            for result in data["storePlatformData"]["lockup"]["results"].values()
            if result["kind"] == "song"
        ]

        # Attempt to match by title & artist
        for song in songs:
            if song["name"].lower() == title.lower() and (
                song["artistName"].lower() in artist.lower()
                or artist.lower() in song["artistName"].lower()
            ):
                return song["id"]

        # Attempt to match by title if we didn't get a title & artist match
        for song in songs:
            if song["name"].lower() == title.lower():
                return song["id"]

    except:
        # We don't do any fancy error handling.. Just return None if something went wrong
        return None


class ResultCache:
    def __init__(self, file_path: Path):
        self.path = file_path
        if self.path.exists():
            with open(self.path, "r") as cache_file:
                print("Loading cache from {}".format(self.path))
                self.cache = json.load(cache_file)
        self.cache = {}

    def put(self, spotify_id, itunes_id):
        self.cache[spotify_id] = itunes_id
        self.save()

    def query(self, spotify_id):
        return self.cache.get(spotify_id)

    def is_cached(self, spotify_id):
        return spotify_id in self.cache

    def save(self):
        with open(self.path, "w") as cache_file:
            json.dump(self.cache, cache_file, indent=4)


def convert(spotify_path: Path, itunes_path: Path, cache: Optional[ResultCache] = None):
    itunes_identifiers = []
    with open(spotify_path, encoding="utf-8") as playlist_file:
        playlist_reader = csv.reader(playlist_file)
        next(playlist_reader)

        for row in playlist_reader:
            spotify_id, title, artist = row[0], row[1], row[2]
            if not cache.is_cached(spotify_id):
                itunes_identifier = retrieve_itunes_identifier(title, artist)
                cache.put(spotify_id, itunes_identifier)
            else:
                itunes_identifier = cache.query(spotify_id)

            if itunes_identifier:
                itunes_identifiers.append(itunes_identifier)
                print("{} - {} => {}".format(title, artist, itunes_identifier))
            else:
                print("{} - {} => Not Found".format(title, artist))
                noresult = "{} - {} => Not Found".format(title, artist)
                with open("noresult.txt", "a+") as f:
                    f.write(noresult)
                    f.write("\n")

    with open(itunes_path, "w", encoding="utf-8") as output_file:
        for itunes_identifier in itunes_identifiers:
            output_file.write(str(itunes_identifier) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spotify_dir", type=Path)
    ap.add_argument("itunes_dir", type=Path)
    args = ap.parse_args()

    spotify_dir = args.spotify_dir
    itunes_dir = args.itunes_dir
    itunes_dir.mkdir(exist_ok=True)

    cache = ResultCache(Path("id_cache.json"))

    for playlist in spotify_dir.glob("*.csv"):
        itunes_playlist = itunes_dir / playlist.name
        convert(playlist, itunes_playlist, cache)


# Developped by @therealmarius on GitHub
# Based on the work of @simonschellaert on GitHub
# Github project page: https://github.com/therealmarius/Spotify-2-AppleMusic
