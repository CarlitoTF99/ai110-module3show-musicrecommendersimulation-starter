  
  #Notes

  
  user_prefs = {
      "favorite_genre": "lofi",
      "favorite_mood": "chill",
      "target_energy": 0.40,
      "target_valence": 0.60,
      "likes_acoustic": True,
  }

  ## Experiment profiles (for Phase 3)
- Conflicting: rock + chill + energy 0.40 + acoustic → tests genre vs. mood/energy
- (add 2 more later, e.g., high-energy pop gym listener, sad acoustic listener)

## Algorithm Recipe
[paste the final recipe block from my last message]

## Expected biases
- Lofi has the most songs AND the most related genres (jazz, ambient)
- Classical, reggae, latin fans get no partial genre credit
- Mood families partly double-count with valence
- A single favorite_genre string leaves most songs at 0 genre points

## Future improvements (from Claude Code critique)
- Multiple weighted genres, e.g. {"rock": 1.0, "lofi": 0.7}
- Disliked genres/moods that subtract points
- Per-user tolerance instead of a fixed σ
- likes_acoustic → target number (None = don't care)
- Artist/genre diversity in the top 5

## Edge-case findings (Phase 4)
- Sad Banger: Rust in the Rain wins (6.13) with energy 0.33 vs target 0.90.
  Ironclad Fury actually sounds right (0.97 energy, 0.18 valence) but is #2 (3.85).
  → labels (4.5) beat sound when genre + mood agree.
- Acoustic Chill Rock: no rock in top 3; Spacewalk Thoughts (ambient) wins.
  → sound beats labels when mood + energy + valence + acoustic agree.
- Ghost Genre (k-pop): fails silently, max possible score drops to 6.0, no warning.
- Silent Classical: "calm" (a family name) matches nothing; Tempest Overture
  ("dramatic", 0.72 energy) wins a request for silent, joyful music at 2.97/8.5.
- Nostalgic Pop: the one "nostalgic" song (folk) beats every pop song.
- Fragile inputs: "likes_acoustic": "no" counts as True; "calm" isn't a valid mood.
- Main finding: label points (4.5) ≈ sound points (4.0), so whichever group
  agrees with itself decides the ranking.