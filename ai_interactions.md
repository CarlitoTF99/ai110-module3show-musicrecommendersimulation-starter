# AI Interactions Log

---

## Agentic Workflow (SF8)

**What task did you give the agent?**

I asked Claude Code (running as an agent in VS Code) to add 4 stretch features
to the recommender on the `stretch-features` branch, one part at a time:
advanced song features, switchable scoring modes, a diversity penalty, and a
summary table. It also had to add tests and update the README, model card and
this file. The main rule was that `python -m src.main` with no flags must give
exactly the same scores and rankings as before, so every new feature had to be
opt-in. After each part it had to run `pytest` and `python -m src.main` and
stop if anything failed.

**Prompts used:**

The key prompt for Part 1 (the full request also covered Parts 2–4, tests and
docs):

> PART 1 — Advanced song features (Challenge 1)
> - Add 5 new columns to data/songs.csv for all 20 songs, with believable values:
>   popularity (0–100 int), release_decade (int, e.g. 1990, 2010),
>   mood_tags (semicolon-separated detailed tags, e.g. "euphoric;nostalgic"),
>   instrumentalness (0–1 float), lyrics_language ("english", "spanish",
>   "instrumental", etc.).
> - Update load_songs to parse them (mood_tags → list of strings), and add them
>   to the Song dataclass WITH DEFAULTS so existing tests still work.
> - Update score_song so these new OPTIONAL user_prefs keys earn points:
>   target_popularity (Gaussian closeness, scaled to 0–1), preferred_decade
>   (full points exact, half for ±10 years), mood_tags (points per overlapping
>   tag, capped), target_instrumentalness (Gaussian), preferred_language (exact).
>   Suggested weights: 0.5–1.0 each; put them in named constants.
>   If a key is ABSENT from user_prefs, that feature adds 0 points, adds no
>   reason line, and is NOT counted in MAX_SCORE for that user — so existing
>   profiles score exactly as before. Make the max score shown per profile
>   reflect only the features that profile uses.
> - Add one new profile to PROFILES in main.py, "Nostalgic Explorer (advanced)",
>   that uses all 5 new keys.

Follow-up prompt: after the agent stopped at Part 3 (see below), I asked it to
report which parts were done and to finish only what was missing: Part 4, the
tests and the docs.

**What did the agent generate or change?**

Files changed:
- `data/songs.csv`: 5 new columns for all 20 songs.
- `src/recommender.py`: new `Song` fields with defaults; `load_songs` parses
  the new columns; `_advanced_parts` and `max_score` for the optional
  features; `ScoringWeights` and `SCORING_MODES` for the modes;
  `_diverse_rerank` and the `diverse` option on `recommend_songs`.
- `src/main.py`: the "Nostalgic Explorer (advanced)" profile, a per-profile max
  score, and `--mode`, `--diverse` and `--table` flags (`print_table` uses
  tabulate with `tablefmt="grid"`).
- `requirements.txt`: added `tabulate`.
- `tests/test_recommender.py`: 5 new tests.
- `README.md`, `model_card.md`, `ai_interactions.md`: documentation using
  real program output.

Commands run:
- `python -m src.main > baseline.txt` once at the start, to save the original
  output.
- After every part: `pytest` and `python -m src.main`, plus a script that
  diffs the new output against the baseline.
- `python -m src.main --mode genre-first | mood-first | energy-focused` to
  confirm each mode changes the rankings.
- `python -m src.main --diverse` and `--table` (alone and combined with
  `--mode` and `--diverse`).
- `pip install tabulate` inside `.venv`.

What it verified automatically:
- The 7 original profiles have identical scores and rankings to the baseline
  after every part (the only differences are the new `mode=` header line and
  the new profile at the end).
- Every reason list adds up to its displayed score: 1,280 checks across all
  profiles, modes and diversity on/off, with 0 mismatches.
- The `--table` output is plain ASCII (no Unicode box characters).
- All 7 tests pass.

Problems the agent ran into:
- One of its scripted edits to `main.py` failed partway through, so `--mode`
  was silently ignored at first. It noticed because every mode printed the
  same results, and it redid the edit.
- It first ran the code with the system Python instead of my `.venv`, then
  switched to `.venv` and rechecked everything.
- **Requirement conflict:** with my penalties (−1.50 artist, −0.75 genre),
  LoRoom still appears twice in Chill Lofi's diverse top 5, because the next
  best song only scores 3.26. So my test "no artist appears twice" couldn't
  pass. The agent stopped and asked me instead of quietly changing the
  numbers. I chose to keep −1.50 and change the test to check that Focus Flow
  is penalized and drops below every other song in the list.

**What did you verify or fix manually?**

### Manual verification (me)

- [x] Ran `python -m src.main` and checked High-Energy Pop #1 is Sunrise City 8.37 / 8.5
- [x] Checked the new CSV values look believable for each song
- [x] Hand-checked one advanced score (Hollow Porch Light, 11.54 / 12)
- [x] Ran each `--mode` and checked the changes make sense
- [x] Compared Chill Lofi with and without `--diverse`
- [x] Ran `--table` in my Windows terminal and checked it displays correctly
- [x] Ran `pytest` myself
- [x] Read through the README, model card and this file

---

## Design Pattern (SF10)

**Which design pattern did you use?**

The **Strategy pattern**, where each strategy is a weight-config object. A
scoring mode is a frozen `ScoringWeights` dataclass, and `SCORING_MODES` maps
each mode name (`balanced`, `genre-first`, `mood-first`, `energy-focused`) to
one of them.

**How did AI help you brainstorm or implement it?**

Before writing code, the agent compared 3 options:
1. **Strategy classes:** an abstract `ScoringStrategy` with one subclass per
   mode that overrides the scoring methods. This needs a lot of code, and each
   subclass would copy or override scoring logic even though only the numbers
   change.
2. **A dict of scoring functions:** one function per mode. That's simpler, but
   it still means 4 copies of the scoring rules that could drift apart.
3. **Strategy as weight-config objects:** one `ScoringWeights` instance per
   mode, and a single `score_song` that reads whatever weights it's given.

It picked option 3 because the modes really only differ in their weights, so
the strategy can be plain data. The scoring rules stay in one function, adding
a mode is one dict entry, and `balanced` is built from the original constants,
so the default can't drift from the original scores.

**How does the pattern appear in your final code?**

- `ScoringWeights` (`src/recommender.py`): the strategy, a frozen dataclass
  with the 7 core weights and a `max_score` property.
- `SCORING_MODES` and `DEFAULT_MODE = "balanced"` (`src/recommender.py`):
  the available strategies, by name.
- `_weights_for(mode)`: looks up a strategy and raises a clear `ValueError`
  for unknown modes.
- `score_song(user_prefs, song, mode)`, `max_score(user_prefs, mode)` and
  `recommend_songs(..., mode=...)`: the context that uses the selected weights.
- `parse_args()` in `src/main.py`: `--mode` with `choices=list(SCORING_MODES)`,
  so the command line always matches the available strategies.
