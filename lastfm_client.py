"""Genre/mood tag lookups via Last.fm.

Spotify stopped returning the `genres` field on artist objects for
Development Mode apps as part of its February 2026 lockdown, so there's no
first-party genre signal left to match moods against. Last.fm's tagging API
is a separate, still-open service with community-contributed tags per
artist (genres, but also mood words like "chill", "sad", "party") that
fills that gap.
"""

import time

import requests

LASTFM_API_URL = "http://ws.audioscrobbler.com/2.0/"
REQUEST_DELAY_SECONDS = 0.3  # stay comfortably under Last.fm's 2 req/sec free-tier limit


def get_tags_for_artists(artist_names_by_id: dict, api_key: str) -> dict:
    """Returns {artist_id: set(lowercase tags)}."""
    tags_by_id = {}
    for artist_id, name in artist_names_by_id.items():
        tags_by_id[artist_id] = _get_artist_tags(name, api_key)
        time.sleep(REQUEST_DELAY_SECONDS)
    return tags_by_id


def _get_artist_tags(artist_name: str, api_key: str) -> set:
    params = {
        "method": "artist.gettoptags",
        "artist": artist_name,
        "api_key": api_key,
        "format": "json",
    }
    try:
        resp = requests.get(LASTFM_API_URL, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        tags = data.get("toptags", {}).get("tag", [])
        return {t["name"].lower() for t in tags if isinstance(t, dict) and t.get("name")}
    except (requests.RequestException, ValueError, KeyError):
        return set()
