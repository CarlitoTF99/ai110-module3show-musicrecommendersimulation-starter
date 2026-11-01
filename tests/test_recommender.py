from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Stretch features ---

from pathlib import Path

from src.recommender import (
    load_songs,
    max_score,
    recommend_songs,
    score_song,
    SCORING_MODES,
)
from src.main import PROFILES

SONGS_CSV = Path(__file__).resolve().parent.parent / "data" / "songs.csv"

HIGH_ENERGY_POP = {
    "favorite_genre": "pop",
    "favorite_mood": "happy",
    "target_energy": 0.80,
    "target_valence": 0.80,
    "likes_acoustic": False,
}


def _song(songs, title):
    return next(song for song in songs if song["title"] == title)


def test_default_scores_unchanged():
    songs = load_songs(SONGS_CSV)
    score, _ = score_song(HIGH_ENERGY_POP, _song(songs, "Sunrise City"))
    assert score == 8.37
    assert max_score(HIGH_ENERGY_POP) == 8.5

    top_song, top_score, _ = recommend_songs(HIGH_ENERGY_POP, songs, k=5)[0]
    assert top_song["title"] == "Sunrise City"
    assert top_score == 8.37


def test_each_mode_returns_results_and_one_changes_a_top_song():
    songs = load_songs(SONGS_CSV)
    default_top = {
        name: recommend_songs(prefs, songs, k=5)[0][0]["title"] for name, prefs in PROFILES.items()
    }
    changed = False
    for mode in SCORING_MODES:
        for name, prefs in PROFILES.items():
            results = recommend_songs(prefs, songs, k=5, mode=mode)
            assert len(results) == 5
            if results[0][0]["title"] != default_top[name]:
                changed = True
    assert changed


def test_diversity_penalizes_repeated_artist_in_chill_lofi():
    songs = load_songs(SONGS_CSV)
    prefs = PROFILES["Chill Lofi"]

    before = recommend_songs(prefs, songs, k=5)
    assert [song["title"] for song, _, _ in before][:3] == ["Library Rain", "Midnight Coding", "Focus Flow"]

    after = recommend_songs(prefs, songs, k=5, diverse=True)
    titles = [song["title"] for song, _, _ in after]
    focus_flow = after[titles.index("Focus Flow")]

    # Focus Flow repeats LoRoom, so it is penalized and drops below every other pick
    assert "diversity penalty: artist LoRoom already in list (-1.50)" in focus_flow[2]
    assert focus_flow[1] == 5.14
    assert titles[-1] == "Focus Flow"
    assert all(score > focus_flow[1] for song, score, _ in after if song["title"] != "Focus Flow")


def test_diversity_reasons_add_up_to_score():
    songs = load_songs(SONGS_CSV)
    for prefs in PROFILES.values():
        for _, score, explanation in recommend_songs(prefs, songs, k=10, diverse=True):
            total = sum(float(reason.rsplit("(", 1)[1].rstrip(")")) for reason in explanation.split("; "))
            assert round(total, 2) == score


def test_advanced_keys_score_matching_song_higher():
    songs = load_songs(SONGS_CSV)
    advanced = PROFILES["Nostalgic Explorer (advanced)"]
    basic = {key: advanced[key] for key in HIGH_ENERGY_POP}
    song = _song(songs, "Hollow Porch Light")

    basic_score, basic_reasons = score_song(basic, song)
    advanced_score, advanced_reasons = score_song(advanced, song)

    assert advanced_score > basic_score
    assert len(advanced_reasons) == len(basic_reasons) + 5
    assert max_score(basic) == 8.5
    assert max_score(advanced) == 12.0
