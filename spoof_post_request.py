import json
import os
from pathlib import Path

import requests

# copied_headers = r"""Accept-Encoding
# gzip, deflate, br

# Scrubbed the following keys before pushing:
# Authorization
# Cookie
# media-user-token

copied_headers = r"""Accept-Language
	en-US,en;q=0.5
Connection
	keep-alive
Content-Length
	45
Content-Type
	text/plain;charset=UTF-8
Host
	amp-api.music.apple.com
Origin
	https://music.apple.com
Referer
	https://music.apple.com/
Sec-Fetch-Dest
	empty
Sec-Fetch-Mode
	cors
Sec-Fetch-Site
	same-site
TE
	trailers
User-Agent
	Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0""".split(
    "\n"
)


headers = {
    key.strip(): value.strip()
    for key, value in zip(copied_headers[::2], copied_headers[1::2])
}
playlist_ids = {}


def build_url_for_add_track(playlist_id: str):
    return f"https://amp-api.music.apple.com/v1/me/library/playlists/p.{playlist_id}/tracks?art[url]=f&l=en-US&representation=resources"


def build_url_for_make_playlist(playlist_name: str):
    return "https://amp-api.music.apple.com/v1/me/library/playlists?art[url]=f&l=en-US"


def make_playlist(playlist_name: str) -> str:
    """Returns the playlist id"""
    url = build_url_for_make_playlist(playlist_name)
    # {"attributes":{"name":"test","description":"","isPublic":false},"relationships":{"tracks":{"data":[{"id":"i.dlvqa0PH6VgpVxk","type":"songs"}]}}}
    body = {
        "attributes": {"name": playlist_name, "description": "", "isPublic": True},
        "relationships": {"tracks": {"data": []}},
    }
    response = requests.post(url, headers=headers, json=body)
    playlist_id = response.json()["data"][0]["id"][2:]  # remove the p. at the start
    return playlist_id


def build_request_data(song: str) -> dict:
    if isinstance(song, list):
        return {"data": [{"id": s, "type": "songs"} for s in song]}
    return {"data": [{"id": song, "type": "songs"}]}


def make_requests(playlist_file: Path):
    with open(playlist_file, "r") as playlist_file:
        lines = playlist_file.readlines()
        playlist_name = lines[0].strip()
        if playlist_name in playlist_ids:
            return
            playlist_id = playlist_name
        else:
            playlist_id = make_playlist(playlist_name)
            playlist_ids[playlist_name] = playlist_id
        songs = list(map(str.strip, lines[1:]))

        url = build_url_for_add_track(playlist_ids[playlist_name])
        data = build_request_data(songs)
        response = requests.post(url, headers=headers, json=data)
        print(response.json())
        print()
        print()


if __name__ == "__main__":
    itunes_dir = Path("itunes_playlists")

    if Path("playlist_ids.json").exists():
        with open("playlist_ids.json", "r") as f:
            playlist_ids = json.load(f)

    for f in itunes_dir.glob("*.txt"):
        make_requests(f)

    with open("playlist_ids.json", "w") as f:
        json.dump(playlist_ids, f, indent=4)
