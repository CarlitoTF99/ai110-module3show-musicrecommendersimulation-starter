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
    GENRE_EXACT_POINTS,
    MOOD_EXACT_POINTS,
    ENERGY_WEIGHT,
    VALENCE_WEIGHT,
    ACOUSTIC_WEIGHT,
)

MAX_SCORE = GENRE_EXACT_POINTS + MOOD_EXACT_POINTS + ENERGY_WEIGHT + VALENCE_WEIGHT + ACOUSTIC_WEIGHT
LINE_WIDTH = 54
NAME_WIDTH = 44


def main() -> None:
    user_prefs = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.80,
        "target_valence": 0.80,
        "likes_acoustic": False,
    }
    songs = load_songs("data/songs.csv")

    print(
        f"Profile: genre={user_prefs['favorite_genre']}"
        f" | mood={user_prefs['favorite_mood']}"
        f" | energy={user_prefs['target_energy']:.2f}"
        f" | valence={user_prefs['target_valence']:.2f}"
        f" | acoustic={'yes' if user_prefs['likes_acoustic'] else 'no'}"
    )
    print(f"Loaded songs: {len(songs)}")

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print(f"\nTop {len(recommendations)} recommendations")
    print("=" * LINE_WIDTH)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        if rank > 1:
            print("-" * LINE_WIDTH)
        name = f"{song['title']} - {song['artist']}"
        print(f"{rank}. {name:<{NAME_WIDTH}}Score: {score:.2f} / {MAX_SCORE:g}")
        for reason in explanation.split("; "):
            print(f"     + {reason}")


if __name__ == "__main__":
    main()
