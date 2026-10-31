import csv
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

# --- Scoring recipe (max 8.5 points) ---
GENRE_EXACT_POINTS = 2.5
GENRE_RELATED_POINTS = 1.25
MOOD_EXACT_POINTS = 2.0
MOOD_FAMILY_POINTS = 1.0
ENERGY_WEIGHT = 2.0
VALENCE_WEIGHT = 1.5
ACOUSTIC_WEIGHT = 0.5
SIGMA = 0.20

DEFAULT_TARGET_VALENCE = 0.6
DEFAULT_LIKES_ACOUSTIC = False

# Symmetric pairs, not chained (lofi~jazz and blues~jazz does not make lofi~blues)
RELATED_GENRES = {
    frozenset(pair)
    for pair in [
        ("pop", "indie pop"),
        ("rock", "metal"),
        ("lofi", "jazz"),
        ("lofi", "ambient"),
        ("electronic", "synthwave"),
        ("folk", "country"),
        ("blues", "jazz"),
        ("hip-hop", "r&b"),
    ]
}

# romantic and nostalgic are intentionally ungrouped
MOOD_FAMILIES = {
    "calm": {"chill", "relaxed", "focused"},
    "bright": {"happy", "carefree", "hopeful"},
    "driven": {"energetic", "intense", "confident"},
    "low": {"sad", "melancholy", "moody"},
    "turbulent": {"angry", "dramatic"},
}

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = DEFAULT_TARGET_VALENCE

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the user's top k Song objects, ranked by score_song."""
        song_dicts = [asdict(song) for song in self.songs]
        # recommend_songs hands back the same dicts it was given, so map them to the original Songs
        by_dict_id = {id(d): song for d, song in zip(song_dicts, self.songs)}
        ranked = recommend_songs(asdict(user), song_dicts, k)
        return [by_dict_id[id(song_dict)] for song_dict, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain a song's score for the user as a "; "-joined string of reasons."""
        _, reasons = score_song(asdict(user), asdict(song))
        return "; ".join(reasons)

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file into dicts, converting numeric columns and raising ValueError on bad rows."""
    int_fields = {"id"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness"}

    songs = []
    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # reader.line_num is the file line of this row (header is line 1)
            line = reader.line_num
            song = {}
            for key, value in row.items():
                value = (value or "").strip()
                if key in int_fields or key in float_fields:
                    if value == "":
                        raise ValueError(f"Row {line}: missing value in column '{key}'")
                    try:
                        song[key] = int(value) if key in int_fields else float(value)
                    except ValueError:
                        raise ValueError(
                            f"Row {line}: non-numeric value {value!r} in column '{key}'"
                        ) from None
                else:
                    # title, artist, genre, mood (and any extra columns) stay strings
                    song[key] = value
            songs.append(song)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against a user's preferences and return (score, reasons)."""
    fav_genre = user_prefs["favorite_genre"].strip().lower()
    fav_mood = user_prefs["favorite_mood"].strip().lower()
    target_energy = _check_unit_range("target_energy", user_prefs["target_energy"])
    target_valence = _check_unit_range(
        "target_valence", user_prefs.get("target_valence", DEFAULT_TARGET_VALENCE)
    )
    likes_acoustic = user_prefs.get("likes_acoustic", DEFAULT_LIKES_ACOUSTIC)

    song_genre = song["genre"].strip().lower()
    song_mood = song["mood"].strip().lower()

    # Each part is rounded before summing so the reasons always add up to the score
    parts = []

    if song_genre == fav_genre:
        parts.append((GENRE_EXACT_POINTS, f"genre match: {song_genre}"))
    elif _genres_related(song_genre, fav_genre):
        parts.append((GENRE_RELATED_POINTS, f"related genre: {song_genre} ~ {fav_genre}"))
    else:
        parts.append((0.0, f"no genre match: {song_genre}"))

    if song_mood == fav_mood:
        parts.append((MOOD_EXACT_POINTS, f"mood match: {song_mood}"))
    elif _same_mood_family(song_mood, fav_mood):
        parts.append((MOOD_FAMILY_POINTS, f"mood family match: {song_mood} ~ {fav_mood}"))
    else:
        parts.append((0.0, f"no mood match: {song_mood}"))

    energy = song["energy"]
    parts.append((
        ENERGY_WEIGHT * _gaussian(energy - target_energy, SIGMA),
        f"energy {energy:.2f} vs target {target_energy:.2f}",
    ))

    valence = song["valence"]
    parts.append((
        VALENCE_WEIGHT * _gaussian(valence - target_valence, SIGMA),
        f"valence {valence:.2f} vs target {target_valence:.2f}",
    ))

    acousticness = song["acousticness"]
    if likes_acoustic:
        parts.append((ACOUSTIC_WEIGHT * acousticness, f"acousticness {acousticness:.2f}, likes acoustic"))
    else:
        parts.append((
            ACOUSTIC_WEIGHT * (1 - acousticness),
            f"acousticness {acousticness:.2f}, prefers non-acoustic",
        ))

    score = 0.0
    reasons = []
    for points, label in parts:
        points = round(points, 2)
        score += points
        reasons.append(f"{label} (+{points:.2f})")
    return round(score, 2), reasons


def _gaussian(d: float, sigma: float) -> float:
    """Return a closeness score in (0, 1] that is 1 when d is 0 and falls off with width sigma."""
    return math.exp(-(d ** 2) / (2 * sigma ** 2))


def _genres_related(a: str, b: str) -> bool:
    """Return True if the two genres are listed as a related pair in RELATED_GENRES."""
    return frozenset((a, b)) in RELATED_GENRES


def _same_mood_family(a: str, b: str) -> bool:
    """Return True if both moods belong to the same family in MOOD_FAMILIES."""
    return any(a in moods and b in moods for moods in MOOD_FAMILIES.values())


def _check_unit_range(name: str, value: float) -> float:
    """Return value as a float, raising ValueError if it is outside [0, 1]."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1, got {value!r}")
    return float(value)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song and return the top k as (song, score, explanation), best first."""
    if k <= 0:
        return []

    target_energy = user_prefs["target_energy"]
    scored = [(song, *score_song(user_prefs, song)) for song in songs]

    # Highest score first; ties go to the closer energy, then the lower id
    ranked = sorted(
        scored,
        key=lambda item: (
            -item[1],
            abs(item[0]["energy"] - target_energy),
            item[0]["id"],
        ),
    )
    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked[:k]]
