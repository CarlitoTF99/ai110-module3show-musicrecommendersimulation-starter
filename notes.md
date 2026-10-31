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