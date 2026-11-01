  
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

## Step 2: Accuracy and surprises

**Intuition check (High-Energy Pop):** Sunrise City at #1 feels right — it's
upbeat, high-energy pop. Rooftop Lights at #2 also fits. Gym Hero at #3 feels
slightly off: it's pop, but "intense" is more workout music than happy music.
Island Slowdown at #4 feels wrong — it's a slow reggae song (energy 0.55) that
only got in because "carefree" counts as related to "happy." Fuego en la Plaza
(#5) actually sounds more like what this listener wants (energy 0.86, valence
0.88), so I'd swap #4 and #5.

**Why Rust in the Rain won Sad Banger:** Rust in the Rain gets 4.50 free label
points (blues +2.50, sad +2.00) that Ironclad Fury gets none of, while Ironclad
Fury only wins back 2.22 on sound (energy +1.85: 1.88 vs 0.03, acousticness
+0.37: 0.48 vs 0.11, valence tied at 1.49). Net: 6.13 − 3.85 = 2.28 points for
Rust in the Rain, even though its energy (0.33) is 0.57 away from the 0.90 target.

**Bug or design?** Working as designed — every point adds up exactly as the
recipe says; the surprise comes from labels (4.5) outweighing energy (max 2.0),
so a song that matches genre + mood can't lose to one that only sounds right.

**Would doubling energy and halving genre flip it?** Yes. With energy 4.0,
genre 1.25, related genre 0.625, Ironclad Fury rises to 5.73 (#1) and Rust in
the Rain drops to 4.92 (#4, behind Storm Runner 5.01 and Night Drive Loop 4.93).

**Why Fuego en la Plaza keeps appearing:** It never earns genre points (latin
has no related genres), but its energy 0.86 and valence 0.88 sit close to the
targets of every upbeat profile, so it collects ~3.3–3.6 sound points almost
for free (plus +1.0 in Deep Intense Rock, where "energetic" is in the same mood
family as "intense"); in Silent Classical it's #3 with only 1.48 because nothing
fits that profile. It's both: the weights let sound points alone carry a song
into the top 5, and with only 20 songs (1–3 per genre) there are few
better-matching songs to push it out after the true matches run out.

**Same song at #1 everywhere?** No — the #1 song is different for every
standard profile (Sunrise City, Library Rain, Storm Runner), so genre is not
overpowering the system. The repetition happens lower in the lists, which
points to the small catalog rather than the genre weight.

## Weight-shift experiment (energy x2, genre x0.5) — result
- Sad Banger flipped: Ironclad Fury 5.73 / 9.25 took #1, Rust in the Rain fell to #4 (4.92); the #1 for High-Energy Pop, Chill Lofi and Deep Intense Rock didn't change.
- Side effects: songs with no matching labels (Storm Runner, Gym Hero, Concrete Psalms) entered top 5s on energy alone, and Tempest Overture lost #1 in Silent Classical.
- Conclusion: it swapped "labels decide" for "energy decides"; weights restored to the original (output matches the baseline exactly), and MAX_SCORE is now computed in recommender.py.
