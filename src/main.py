"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import (
    load_songs,
    recommend_songs,
    MAX_SCORE,
    DEFAULT_TARGET_VALENCE,
    DEFAULT_LIKES_ACOUSTIC,
)

LINE_WIDTH = 54
NAME_WIDTH = 44


PROFILES = {
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.80,
        "target_valence": 0.80,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.40,
        "target_valence": 0.60,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.90,
        "target_valence": 0.40,
        "likes_acoustic": False,
    },
    "Sad Banger (edge case)": {
        "favorite_genre": "blues",
        "favorite_mood": "sad",
        "target_energy": 0.90,
        "target_valence": 0.20,
        "likes_acoustic": False,
    },
    "Acoustic Chill Rock (edge case)": {
        "favorite_genre": "rock",
        "favorite_mood": "chill",
        "target_energy": 0.20,
        "target_valence": 0.60,
        "likes_acoustic": True,
    },
    "Ghost Genre (edge case)": {
        "favorite_genre": "k-pop",
        "favorite_mood": "happy",
        "target_energy": 0.80,
        "target_valence": 0.80,
        "likes_acoustic": False,
    },
    "Silent Classical (edge case)": {
        "favorite_genre": "classical",
        "favorite_mood": "calm",
        "target_energy": 0.0,
        "target_valence": 1.0,
        "likes_acoustic": True,
    },
}


def print_recommendations(name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    print("#" * LINE_WIDTH)
    print(f"PROFILE: {name}")
    print(
        f"genre={user_prefs['favorite_genre']}"
        f" | mood={user_prefs['favorite_mood']}"
        f" | energy={user_prefs['target_energy']:.2f}"
        f" | valence={user_prefs.get('target_valence', DEFAULT_TARGET_VALENCE):.2f}"
        f" | acoustic={'yes' if user_prefs.get('likes_acoustic', DEFAULT_LIKES_ACOUSTIC) else 'no'}"
    )
    print("#" * LINE_WIDTH)

    recommendations = recommend_songs(user_prefs, songs, k=k)

    print(f"\nTop {len(recommendations)} recommendations")
    print("=" * LINE_WIDTH)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        if rank > 1:
            print("-" * LINE_WIDTH)
        title = f"{song['title']} - {song['artist']}"
        print(f"{rank}. {title:<{NAME_WIDTH}}Score: {score:.2f} / {MAX_SCORE:g}")
        for reason in explanation.split("; "):
            print(f"     + {reason}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    for name, user_prefs in PROFILES.items():
        print_recommendations(name, user_prefs, songs)
        print()


if __name__ == "__main__":
    main()
