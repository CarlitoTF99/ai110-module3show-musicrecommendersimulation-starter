import csv
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict, field

# --- Scoring recipe (max score is MAX_SCORE below) ---
GENRE_EXACT_POINTS = 2.5
GENRE_RELATED_POINTS = 1.25
MOOD_EXACT_POINTS = 2.0
MOOD_FAMILY_POINTS = 1.0
ENERGY_WEIGHT = 2.0
VALENCE_WEIGHT = 1.5
ACOUSTIC_WEIGHT = 0.5
SIGMA = 0.20

MAX_SCORE = GENRE_EXACT_POINTS + MOOD_EXACT_POINTS + ENERGY_WEIGHT + VALENCE_WEIGHT + ACOUSTIC_WEIGHT

# --- Advanced features (opt-in: each only counts when its user_prefs key is present) ---
POPULARITY_WEIGHT = 0.5
DECADE_EXACT_POINTS = 0.75
DECADE_NEAR_POINTS = 0.375   # release decade within +/-10 years
MOOD_TAG_POINTS = 0.35       # per overlapping tag
MOOD_TAGS_MAX_POINTS = 1.0
INSTRUMENTALNESS_WEIGHT = 0.75
LANGUAGE_POINTS = 0.5

# --- Diversity re-rank (opt-in, applied in recommend_songs, not score_song) ---
ARTIST_REPEAT_PENALTY = 1.5
GENRE_REPEAT_PENALTY = 0.75
GENRE_REPEAT_LIMIT = 2       # penalize once the genre already appears this many times


@dataclass(frozen=True)
class ScoringWeights:
    """A ranking strategy: the weights score_song uses. Modes differ only in these numbers."""
    genre_exact: float
    genre_related: float
    mood_exact: float
    mood_family: float
    energy: float
    valence: float
    acoustic: float

    @property
    def max_score(self) -> float:
        """Return the best possible score from the five core features."""
        return self.genre_exact + self.mood_exact + self.energy + self.valence + self.acoustic


DEFAULT_MODE = "balanced"

# Every mode keeps the same 8.5-point ceiling so scores stay comparable across modes
SCORING_MODES = {
    "balanced": ScoringWeights(
        genre_exact=GENRE_EXACT_POINTS,
        genre_related=GENRE_RELATED_POINTS,
        mood_exact=MOOD_EXACT_POINTS,
        mood_family=MOOD_FAMILY_POINTS,
        energy=ENERGY_WEIGHT,
        valence=VALENCE_WEIGHT,
        acoustic=ACOUSTIC_WEIGHT,
    ),
    "genre-first": ScoringWeights(
        genre_exact=4.0, genre_related=2.0, mood_exact=1.5, mood_family=0.75,
        energy=1.5, valence=1.0, acoustic=0.5,
    ),
    "mood-first": ScoringWeights(
        genre_exact=1.5, genre_related=0.75, mood_exact=3.5, mood_family=1.75,
        energy=1.5, valence=1.5, acoustic=0.5,
    ),
    "energy-focused": ScoringWeights(
        genre_exact=1.5, genre_related=0.75, mood_exact=1.5, mood_family=0.75,
        energy=4.0, valence=1.0, acoustic=0.5,
    ),
}

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
    popularity: int = 50
    release_decade: int = 2020
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    lyrics_language: str = "english"

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
    int_fields = {"id", "popularity", "release_decade"}
    float_fields = {"energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness"}

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
                elif key == "mood_tags":
                    song[key] = _parse_tags(value)
                else:
                    # title, artist, genre, mood (and any extra columns) stay strings
                    song[key] = value
            songs.append(song)
    return songs

def score_song(user_prefs: Dict, song: Dict, mode: str = DEFAULT_MODE) -> Tuple[float, List[str]]:
    """Score one song against a user's preferences with the given mode's weights and return (score, reasons)."""
    weights = _weights_for(mode)
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
        parts.append((weights.genre_exact, f"genre match: {song_genre}"))
    elif _genres_related(song_genre, fav_genre):
        parts.append((weights.genre_related, f"related genre: {song_genre} ~ {fav_genre}"))
    else:
        parts.append((0.0, f"no genre match: {song_genre}"))

    if song_mood == fav_mood:
        parts.append((weights.mood_exact, f"mood match: {song_mood}"))
    elif _same_mood_family(song_mood, fav_mood):
        parts.append((weights.mood_family, f"mood family match: {song_mood} ~ {fav_mood}"))
    else:
        parts.append((0.0, f"no mood match: {song_mood}"))

    energy = song["energy"]
    parts.append((
        weights.energy * _gaussian(energy - target_energy, SIGMA),
        f"energy {energy:.2f} vs target {target_energy:.2f}",
    ))

    valence = song["valence"]
    parts.append((
        weights.valence * _gaussian(valence - target_valence, SIGMA),
        f"valence {valence:.2f} vs target {target_valence:.2f}",
    ))

    acousticness = song["acousticness"]
    if likes_acoustic:
        parts.append((weights.acoustic * acousticness, f"acousticness {acousticness:.2f}, likes acoustic"))
    else:
        parts.append((
            weights.acoustic * (1 - acousticness),
            f"acousticness {acousticness:.2f}, prefers non-acoustic",
        ))

    parts.extend(_advanced_parts(user_prefs, song))

    score = 0.0
    reasons = []
    for points, label in parts:
        points = round(points, 2)
        score += points
        reasons.append(f"{label} (+{points:.2f})")
    return round(score, 2), reasons


def _advanced_parts(user_prefs: Dict, song: Dict) -> List[Tuple[float, str]]:
    """Score the optional advanced features; a feature whose user_prefs key is absent adds nothing."""
    parts = []

    if user_prefs.get("target_popularity") is not None:
        target = user_prefs["target_popularity"]
        popularity = song["popularity"]
        parts.append((
            POPULARITY_WEIGHT * _gaussian((popularity - target) / 100, SIGMA),
            f"popularity {popularity} vs target {target}",
        ))

    if user_prefs.get("preferred_decade") is not None:
        target = user_prefs["preferred_decade"]
        decade = song["release_decade"]
        if decade == target:
            parts.append((DECADE_EXACT_POINTS, f"decade match: {decade}s"))
        elif abs(decade - target) == 10:
            parts.append((DECADE_NEAR_POINTS, f"near decade: {decade}s ~ {target}s"))
        else:
            parts.append((0.0, f"no decade match: {decade}s"))

    if user_prefs.get("mood_tags") is not None:
        wanted = _parse_tags(user_prefs["mood_tags"])
        shared = [tag for tag in song["mood_tags"] if tag in wanted]
        points = min(MOOD_TAGS_MAX_POINTS, MOOD_TAG_POINTS * len(shared))
        label = f"mood tags: {', '.join(shared)}" if shared else "no mood tag overlap"
        parts.append((points, label))

    if user_prefs.get("target_instrumentalness") is not None:
        target = _check_unit_range("target_instrumentalness", user_prefs["target_instrumentalness"])
        instrumentalness = song["instrumentalness"]
        parts.append((
            INSTRUMENTALNESS_WEIGHT * _gaussian(instrumentalness - target, SIGMA),
            f"instrumentalness {instrumentalness:.2f} vs target {target:.2f}",
        ))

    if user_prefs.get("preferred_language") is not None:
        target = user_prefs["preferred_language"].strip().lower()
        language = song["lyrics_language"].strip().lower()
        if language == target:
            parts.append((LANGUAGE_POINTS, f"language match: {language}"))
        else:
            parts.append((0.0, f"no language match: {language}"))

    return parts


def max_score(user_prefs: Dict, mode: str = DEFAULT_MODE) -> float:
    """Return the highest score possible for this user, counting only the advanced features they use."""
    total = _weights_for(mode).max_score
    if user_prefs.get("target_popularity") is not None:
        total += POPULARITY_WEIGHT
    if user_prefs.get("preferred_decade") is not None:
        total += DECADE_EXACT_POINTS
    if user_prefs.get("mood_tags") is not None:
        wanted = _parse_tags(user_prefs["mood_tags"])
        total += min(MOOD_TAGS_MAX_POINTS, MOOD_TAG_POINTS * len(wanted))
    if user_prefs.get("target_instrumentalness") is not None:
        total += INSTRUMENTALNESS_WEIGHT
    if user_prefs.get("preferred_language") is not None:
        total += LANGUAGE_POINTS
    return round(total, 2)


def _weights_for(mode: str) -> ScoringWeights:
    """Return the ScoringWeights for a mode name, raising ValueError for unknown modes."""
    try:
        return SCORING_MODES[mode]
    except KeyError:
        raise ValueError(f"Unknown mode {mode!r}; choose from {', '.join(SCORING_MODES)}") from None


def _parse_tags(value) -> List[str]:
    """Return lowercase tags from a list or a semicolon-separated string, dropping blanks."""
    if isinstance(value, str):
        value = value.split(";")
    return [tag.strip().lower() for tag in value if tag.strip()]


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

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = DEFAULT_MODE,
    diverse: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """Score every song with the mode's weights and return the top k as (song, score, explanation), best first.

    With diverse=True, songs are picked greedily and penalized for repeating an artist or genre already picked.
    """
    if k <= 0:
        return []

    target_energy = user_prefs["target_energy"]
    scored = [(song, *score_song(user_prefs, song, mode)) for song in songs]

    # Highest score first; ties go to the closer energy, then the lower id
    def rank_key(item):
        return (-item[1], abs(item[0]["energy"] - target_energy), item[0]["id"])

    if not diverse:
        ranked = sorted(scored, key=rank_key)[:k]
    else:
        ranked = _diverse_rerank(scored, k, rank_key)
    return [(song, score, "; ".join(reasons)) for song, score, reasons in ranked]


def _diverse_rerank(scored: List[Tuple[Dict, float, List[str]]], k: int, rank_key) -> List[Tuple[Dict, float, List[str]]]:
    """Pick k songs one at a time, re-scoring the rest with penalties for artists and genres already picked."""
    remaining = list(scored)
    picked = []
    while remaining and len(picked) < k:
        artists = {song["artist"] for song, _, _ in picked}
        genre_counts = {}
        for song, _, _ in picked:
            genre_counts[song["genre"]] = genre_counts.get(song["genre"], 0) + 1

        candidates = []
        for item in remaining:
            song, score, reasons = item
            penalties = []
            if song["artist"] in artists:
                penalties.append((
                    ARTIST_REPEAT_PENALTY,
                    f"diversity penalty: artist {song['artist']} already in list",
                ))
            count = genre_counts.get(song["genre"], 0)
            if count >= GENRE_REPEAT_LIMIT:
                penalties.append((
                    GENRE_REPEAT_PENALTY,
                    f"diversity penalty: genre {song['genre']} already appears {count} times",
                ))
            adjusted = round(score - sum(points for points, _ in penalties), 2)
            new_reasons = reasons + [f"{label} (-{points:.2f})" for points, label in penalties]
            candidates.append((item, (song, adjusted, new_reasons)))

        original, best = min(candidates, key=lambda pair: rank_key(pair[1]))
        remaining = [item for item in remaining if item is not original]
        picked.append(best)
    return picked
