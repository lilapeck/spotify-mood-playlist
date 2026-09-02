import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from lastfm_client import get_tags_for_artists
from mood_engine import get_target_genres, score_track
from spotify_client import create_mood_playlist, get_candidate_tracks

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

SCOPE = "user-top-read user-library-read playlist-modify-private"
REDIRECT_URI = "http://127.0.0.1:8888/callback"
PLAYLIST_SIZE = 20


def make_sp_oauth():
    return SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=".spotify_cache",
    )


@app.route("/")
def index():
    token_info = make_sp_oauth().get_cached_token()
    return render_template("index.html", logged_in=bool(token_info))


@app.route("/login")
def login():
    return redirect(make_sp_oauth().get_authorize_url())


@app.route("/callback")
def callback():
    code = request.args.get("code")
    make_sp_oauth().get_access_token(code)
    return redirect(url_for("index"))


@app.route("/generate", methods=["POST"])
def generate():
    token_info = make_sp_oauth().get_cached_token()
    if not token_info:
        return redirect(url_for("login"))
    sp = spotipy.Spotify(auth=token_info["access_token"])

    mood_text = request.form.get("mood", "").strip()
    pool = request.form.get("pool", "top_tracks")

    if not mood_text:
        return render_template("index.html", logged_in=True, error="Describe a mood or vibe first.")

    tracks = get_candidate_tracks(sp, pool=pool, limit=60)
    if not tracks:
        source = "saved tracks" if pool == "saved" else "top tracks"
        return render_template("index.html", logged_in=True, error=f"No {source} found on your account to draw from.")

    artist_names_by_id = {a["id"]: a["name"] for t in tracks for a in t["artists"]}
    tags_by_artist = get_tags_for_artists(artist_names_by_id, os.environ["LASTFM_API_KEY"])
    target_genres = get_target_genres(mood_text)

    scored = []
    for t in tracks:
        track_tags = set()
        for a in t["artists"]:
            track_tags |= tags_by_artist.get(a["id"], set())
        scored.append((score_track(track_tags, target_genres, t["popularity"]), t))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_tracks = [t for _, t in scored[:PLAYLIST_SIZE]]

    playlist = create_mood_playlist(sp, f"Mood: {mood_text[:60]}", [t["uri"] for t in top_tracks])

    return render_template(
        "result.html",
        mood=mood_text,
        tracks=top_tracks,
        playlist_url=playlist["external_urls"]["spotify"],
    )


if __name__ == "__main__":
    app.run(port=8888, debug=True)
