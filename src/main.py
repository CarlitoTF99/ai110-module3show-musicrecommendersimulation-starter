"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse

from src.recommender import (
    load_songs,
    recommend_songs,
    max_score,
    DEFAULT_MODE,
    SCORING_MODES,
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
    "Nostalgic Explorer (advanced)": {
        "favorite_genre": "folk",
        "favorite_mood": "nostalgic",
        "target_energy": 0.55,
        "target_valence": 0.55,
        "likes_acoustic": True,
        "target_popularity": 40,
        "preferred_decade": 1970,
        "mood_tags": ["nostalgic", "warm", "wistful"],
        "target_instrumentalness": 0.15,
        "preferred_language": "english",
    },
}

ADVANCED_KEYS = (
    "target_popularity",
    "preferred_decade",
    "mood_tags",
    "target_instrumentalness",
    "preferred_language",
)


def print_recommendations(
    name: str,
    user_prefs: dict,
    songs: list,
    k: int = 5,
    mode: str = DEFAULT_MODE,
    diverse: bool = False,
    table: bool = False,
) -> None:
    print("#" * LINE_WIDTH)
    print(f"PROFILE: {name}")
    print(
        f"genre={user_prefs['favorite_genre']}"
        f" | mood={user_prefs['favorite_mood']}"
        f" | energy={user_prefs['target_energy']:.2f}"
        f" | valence={user_prefs.get('target_valence', DEFAULT_TARGET_VALENCE):.2f}"
        f" | acoustic={'yes' if user_prefs.get('likes_acoustic', DEFAULT_LIKES_ACOUSTIC) else 'no'}"
    )
    advanced = [
        f"{key}={';'.join(value) if isinstance(value, list) else value}"
        for key in ADVANCED_KEYS
        if (value := user_prefs.get(key)) is not None
    ]
    if advanced:
        print(" | ".join(advanced))
    print(f"mode={mode}" + (" | diversity=on" if diverse else ""))
    print("#" * LINE_WIDTH)

    best = max_score(user_prefs, mode)
    recommendations = recommend_songs(user_prefs, songs, k=k, mode=mode, diverse=diverse)

    print(f"\nTop {len(recommendations)} recommendations")
    if table:
        print_table(recommendations, best)
        return

    print("=" * LINE_WIDTH)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        if rank > 1:
            print("-" * LINE_WIDTH)
        title = f"{song['title']} - {song['artist']}"
        print(f"{rank}. {title:<{NAME_WIDTH}}Score: {score:.2f} / {best:g}")
        for reason in explanation.split("; "):
            print(f"     + {reason}")


def print_table(recommendations: list, best: float) -> None:
    # Imported here so the default text output doesn't need tabulate installed
    from tabulate import tabulate

    rows = [
        [rank, song["title"], song["artist"], f"{score:.2f} / {best:g}", explanation.replace("; ", "\n")]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]
    print(tabulate(rows, headers=["Rank", "Title", "Artist", "Score", "Reasons"], tablefmt="grid"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the music recommender on every profile.")
    parser.add_argument(
        "--mode",
        choices=list(SCORING_MODES),
        default=DEFAULT_MODE,
        help=f"ranking strategy (default: {DEFAULT_MODE})",
    )
    parser.add_argument(
        "--diverse",
        action="store_true",
        help="penalize repeated artists and genres in each top-k list",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="show each top-k list as an ASCII grid table",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}\n")

    for name, user_prefs in PROFILES.items():
        print_recommendations(
            name, user_prefs, songs, mode=args.mode, diverse=args.diverse, table=args.table
        )
        print()


if __name__ == "__main__":
    main()
