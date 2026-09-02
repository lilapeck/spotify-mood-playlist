# Mood Playlist Generator

Type a mood or vibe ("rainy day coding, low-key but not sad") and it builds a
private Spotify playlist from your own top tracks or saved library, ranked by
how well each track's artist genres match the mood.

## Why Last.fm tags instead of Spotify audio features

Spotify's `audio-features` and `recommendations` endpoints (valence, energy,
danceability, etc.) were restricted to legacy apps in November 2024, and its
February 2026 Development Mode migration went further and stripped the
`genres` field from the artist endpoint too — every artist now comes back
with `genres: null`. There's no first-party signal left to match a mood
against for a newly-created app, so this pulls genre/mood tags from Last.fm
instead, a separate service with community-contributed tags per artist:

1. `mood_engine.get_target_genres()` maps free-text mood input to a set of
   target genre/mood keywords via lexicon lookup, with a sentiment/energy-word
   fallback for moods that don't hit the lexicon directly.
2. Candidate tracks (your top tracks or saved library) are pulled via
   Spotify's Web API. Each unique artist is then looked up on Last.fm
   (`artist.getTopTags`) to get real tags like "chillwave", "sad", "party".
3. `mood_engine.score_track()` ranks tracks by substring overlap between
   their artists' Last.fm tags and the target keywords, using popularity
   only as a tiebreaker.
4. The top 20 are written to a new private playlist on your account via
   `POST /me/playlists` (Spotify's Feb 2026 migration also removed the old
   `/users/{id}/playlists` endpoint in favor of this one).

Two Spotify API breakages found and worked around during this build:
batch artist lookups (`GET /v1/artists`) are gone for Development Mode apps,
so genre/tag lookups go one artist at a time; and playlist creation moved
from a user-scoped endpoint to `/me/playlists`.

## Setup

1. Create a Spotify app at https://developer.spotify.com/dashboard with
   redirect URI `http://127.0.0.1:8888/callback`.
2. Create a free Last.fm API key at https://www.last.fm/api/account/create.
3. `cp .env.example .env` and fill in your Spotify Client ID/Secret, Last.fm
   API key, and any random string for `FLASK_SECRET_KEY`.
4. `python3 -m venv venv && source venv/bin/activate`
5. `pip install -r requirements.txt`
6. `python app.py`
7. Open http://127.0.0.1:8888, click **Connect Spotify**, then describe a
   mood and generate. Generation takes a few seconds longer than you'd
   expect — that's the sequential Last.fm tag lookups respecting its
   free-tier rate limit.

## Possible extensions

- Swap the keyword lexicon for an LLM call that maps mood text to target
  genres/keywords more flexibly.
- Cache artist genre lookups across requests instead of refetching per run.
- Let the user pick playlist length and public/private.
