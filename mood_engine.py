"""Maps a free-text mood description to target genres and scores tracks against it.

Spotify deprecated the audio-features and recommendations endpoints for all
apps created after November 2024, so this doesn't use numeric features like
valence/energy. Instead it matches on artist genres, which are still exposed
by the standard Web API.
"""

import re

MOOD_GENRE_MAP = {
    "chill": {"chill", "lo-fi", "lofi", "ambient", "acoustic", "soul", "jazz", "bossa nova", "downtempo"},
    "relax": {"ambient", "acoustic", "new age", "piano", "classical", "chillhop"},
    "calm": {"ambient", "classical", "piano", "new age", "acoustic"},
    "focus": {"instrumental", "lo-fi", "lofi", "classical", "ambient", "post-rock"},
    "study": {"instrumental", "lo-fi", "lofi", "classical", "ambient"},
    "coding": {"instrumental", "lo-fi", "lofi", "ambient", "electronic", "post-rock"},
    "happy": {"pop", "dance pop", "funk", "disco", "tropical house", "indie pop"},
    "upbeat": {"pop", "dance", "edm", "funk", "disco", "house"},
    "sad": {"singer-songwriter", "indie folk", "emo", "blues", "slowcore"},
    "melancholy": {"indie folk", "dream pop", "slowcore", "ambient", "shoegaze"},
    "workout": {"edm", "hip hop", "trap", "pop rap", "dance", "house", "dubstep"},
    "gym": {"edm", "hip hop", "trap", "dance", "house"},
    "party": {"dance pop", "edm", "hip hop", "reggaeton", "house", "disco"},
    "angry": {"metal", "punk", "hardcore", "industrial", "nu metal"},
    "intense": {"metal", "industrial", "hardcore", "drum and bass"},
    "romantic": {"r&b", "soul", "soft pop", "quiet storm"},
    "road trip": {"classic rock", "indie rock", "pop rock", "country"},
    "rainy": {"lo-fi", "ambient", "jazz", "acoustic", "indie folk"},
    "morning": {"acoustic", "indie pop", "folk", "soul"},
    "night": {"chillwave", "synthwave", "r&b", "ambient", "downtempo"},
    "sleepy": {"ambient", "classical", "piano", "new age"},
}

POSITIVE_WORDS = {"happy", "joy", "excited", "energetic", "fun", "bright", "hype", "pumped", "good", "great"}
NEGATIVE_WORDS = {"sad", "down", "blue", "heartbroken", "lonely", "tired", "gloomy", "low", "depressed"}
HIGH_ENERGY_WORDS = {"intense", "hype", "pumped", "fast", "hard", "aggressive", "workout", "gym", "party"}
LOW_ENERGY_WORDS = {"chill", "calm", "relax", "slow", "mellow", "soft", "quiet", "sleepy", "low-key", "lowkey"}


def get_target_genres(mood_text: str) -> set:
    text = mood_text.lower()
    words = set(re.findall(r"[a-z']+", text))

    target = set()
    for key, genres in MOOD_GENRE_MAP.items():
        if " " in key:
            if key in text:
                target |= genres
        elif key in words:
            target |= genres

    if target:
        return target

    # Fallback: no direct keyword hit, infer from sentiment/energy words instead.
    positive = bool(words & POSITIVE_WORDS)
    negative = bool(words & NEGATIVE_WORDS)
    high_energy = bool(words & HIGH_ENERGY_WORDS)
    low_energy = bool(words & LOW_ENERGY_WORDS)

    if positive and high_energy:
        return MOOD_GENRE_MAP["happy"] | MOOD_GENRE_MAP["workout"]
    if positive and low_energy:
        return MOOD_GENRE_MAP["happy"] | MOOD_GENRE_MAP["chill"]
    if negative and low_energy:
        return MOOD_GENRE_MAP["sad"] | MOOD_GENRE_MAP["chill"]
    if negative:
        return MOOD_GENRE_MAP["sad"]
    if high_energy:
        return MOOD_GENRE_MAP["workout"]
    if low_energy:
        return MOOD_GENRE_MAP["chill"]

    # Total fallback: broad, generally-liked genres so we still return something.
    return {"pop", "indie pop", "alternative"}


def score_track(track_tags: set, target_genres: set, popularity: int) -> float:
    if target_genres and track_tags:
        # Substring match rather than exact-set: Last.fm tags are free-form
        # ("chillwave", "sad indie") rather than a fixed taxonomy, so exact
        # equality against our lexicon keywords would miss most real tags.
        matches = sum(
            1
            for target in target_genres
            for tag in track_tags
            if target in tag or tag in target
        )
        base = matches / len(target_genres)
    else:
        base = 0.0
    # Popularity is a small tiebreaker only, never the primary signal.
    return base * 10 + (popularity / 100) * 0.5
