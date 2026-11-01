# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**, a content-based music recommender simulation.

---

## 2. Goal / Task

VibeMatch suggests the top 5 songs from a 20-song catalog that best fit one
listener. The listener describes their taste with a favorite genre, a mood, how
energetic and how positive they want the music to be, and whether they like
acoustic songs. Every song gets a score out of 8.5, and each recommendation
comes with the reasons behind its score.

---

## 3. Data Used

- **20 songs.** The starter catalog had 10, and I added 10 more to cover
  missing genres and moods.
- **17 genres:** lofi (3 songs), pop (2), and 1 song each for rock, metal,
  indie pop, ambient, jazz, blues, synthwave, electronic, folk, country,
  hip-hop, r&b, classical, reggae and latin.
- **16 moods:** chill (3 songs), happy (2), intense (2), and 1 song each for
  relaxed, focused, moody, sad, melancholy, angry, dramatic, confident,
  energetic, hopeful, carefree, romantic and nostalgic.
- **5 scored features:** genre, mood, energy, valence and acousticness.
- **2 unscored features:** tempo_bpm and danceability. They're in the data, but
  in this catalog they move almost exactly with energy, so scoring them would
  count the same thing twice.
- **5 advanced features (stretch, opt-in):** these only earn points when a
  listener's profile asks for them.
  - *popularity* (0–100): how well-known the song is.
  - *release_decade* (e.g. 1970, 2010): when it came out.
  - *mood_tags* (e.g. "nostalgic;wistful;warm"): more detailed moods than the
    single mood label, 3 per song.
  - *instrumentalness* (0–1): how much of the song has no vocals.
  - *lyrics_language*: english (12 songs), instrumental (7) or spanish (1).
- **Limits:**
  - Most genres have only 1 song, so most fans get one match or none.
  - Lofi is over-represented: 3 songs plus 2 related genres (jazz, ambient).
  - No lyrics or listening history. The popularity, decade, tag and language
    values are made up by me, not measured.
  - Only one non-English song, so a language preference other than English or
    instrumental can match at most 1 song.
  - The songs and artists are made up, not real tracks.

---

## 4. Algorithm Summary

VibeMatch looks at every song in the catalog, gives each one a score out of
8.5 points based on how well it fits what the listener asked for, and then
shows the highest-scoring songs first.

**What it knows about each song:** its genre, its mood, and three sound
measurements, all on a 0-to-1 scale: *energy* (how intense it feels),
*valence* (how happy or positive it sounds), and *acousticness* (acoustic
instruments vs. electronic sound).

**What it knows about the listener:** their favorite genre, the mood they want,
how energetic and how positive they want the music to be, and whether they like
acoustic songs.

**How a song earns points:**
- **Genre (up to 2.5):** full points for the exact genre, half points for a
  closely related one (for example, indie pop for a pop fan).
- **Mood (up to 2.0):** full points for the exact mood, half points for a mood
  in the same "family" (for example, focused or relaxed for someone who wants
  chill).
- **Energy (up to 2.0) and valence (up to 1.5):** the closer the song is to what
  the listener wants, the more points it gets. A song that's almost exactly
  right gets nearly full points, and the points fall off quickly as it gets
  further away. Being *close* matters, not being higher or lower.
- **Acousticness (up to 0.5):** a small bonus for acoustic songs if the listener
  likes them, or for electronic songs if they don't.

**How it picks the final list:** after every song has a score, it sorts them from
highest to lowest, breaks ties by picking the song whose energy is closest to
the listener's, and shows the top 5. Every recommendation lists exactly where
its points came from, so the listener can see *why* it was chosen.

**What changed from the starter logic:** the starter suggested a simple rule
(+2 for genre, +1 for mood, plus an energy bonus). I gave mood more weight,
added valence and acousticness, and added partial credit for related genres and
similar moods. My data analysis showed that genre labels are sparse (most genres
have only one song) and mood labels are inconsistent, so relying mostly on genre
would leave most of the catalog with almost no points. I also left out tempo and
danceability because in this dataset they move almost exactly with energy, and
scoring them would count the same thing several times.

---

## 5. Observed Behavior / Biases

The biggest weakness is that label points (genre + mood, up to 4.5) and sound
points (energy, valence and acousticness, up to 4.0) are almost equal, so
whichever group agrees with itself decides the ranking. In the Sad Banger
profile (blues, sad, energy 0.90), Rust in the Rain wins with 6.13 because it
matches both labels for 4.5 points, even though its energy is only 0.33. That's
a quiet song for someone who asked for a loud one, and it earns just 0.03 of the
2.0 energy points. The opposite happens in Acoustic Chill Rock: quiet, chill,
acoustic songs win on mood and sound, and the only rock song (Storm Runner)
lands at #6 with 3.80, so a rock fan gets no rock at all. Neither result is a
bug, since the points add up exactly as designed, but the system can't tell
which preference matters most to the listener and quietly picks one for them.

Other biases I found:

- **Genre imbalance:** lofi has 3 songs, pop has 2, and the other 15 genres
  have 1 song each. A lofi or jazz fan has 5 songs that can earn genre points
  (exact or related), but classical, reggae and latin fans have only 1 because
  those genres have no related genres.
- **Extreme energy targets are underserved:** no song has energy below 0.28,
  and energy points drop by half once a song is 0.235 away from the target. A
  listener who wants energy 0.0 can get at most 0.75 of 2.0 energy points,
  which is part of why Silent Classical's #1 scores only 2.97 / 8.5.
- **Mood and valence count the same feeling twice:** "low" moods (sad,
  melancholy, moody) all have valence 0.22–0.49, and "bright" moods (happy,
  carefree, hopeful) have valence 0.70–0.85. So a mood match almost always
  comes with a valence match too. Rust in the Rain gets 2.0 + 1.49 = 3.49
  points for being sad, while energy can never be worth more than 2.0.
- **Silent failure for unknown labels:** "k-pop" matches no song, so the
  highest possible score drops from 8.5 to 6.0. "calm" is the name of a mood
  family, not a mood, so it matches nothing and Silent Classical's ceiling
  drops to 6.5. In both cases the system shows no warning.
- **Same songs keep appearing:** across the 7 test profiles, Fuego en la Plaza
  is in the top 5 four times, and Gym Hero, Island Slowdown, Spacewalk
  Thoughts and Coffee Shop Stories three times each. Meanwhile Hollow Porch
  Light, Velvet Hours and Dust Road Letters never appear at all.

### Fairness: diversity penalty

The optional `--diverse` re-rank fights filter bubbles by taking points away
from a song whose artist is already in the list (−1.50) or whose genre already
appears twice (−0.75), so one artist or style can't fill the whole top 5. In
Chill Lofi, LoRoom's Focus Flow is the second LoRoom song and the third lofi
song, so it drops from #3 (7.39) to #5 (5.14), and Spacewalk Thoughts (ambient)
and Coffee Shop Stories (jazz) move up to #3 and #4. The trade-off is that a
song that matches the listener better can be pushed below one that matches
worse: Focus Flow actually fits Chill Lofi better than both of those songs
before the penalty. In this small catalog the penalty only reorders the list,
because no other song scores above 3.26 for this listener, so LoRoom still
appears twice.

### What works well

- **Normal profiles get sensible lists.** All 5 of Chill Lofi's songs are
  calm and quiet (energy 0.28–0.42, moods chill, focused or relaxed), and each
  normal profile gets a different, near-perfect #1 (8.33–8.37 out of 8.5).
- **The reasons always add up.** Every recommendation lists where its points
  came from, and those points add up to the score exactly (checked for all 140
  song/profile pairs).
- **Results are the same every run.** There's no randomness, and ties are broken
  the same way every time, so the same profile always gets the same list.

---

## 6. Evaluation Process

### Profiles tested

I tested 7 listener profiles: 3 normal ones and 4 "edge cases" built to trick
the scoring.

1. **High-Energy Pop:** pop, happy, energy 0.80, valence 0.80, not acoustic
2. **Chill Lofi:** lofi, chill, energy 0.40, valence 0.60, acoustic
3. **Deep Intense Rock:** rock, intense, energy 0.90, valence 0.40, not acoustic
4. **Sad Banger (edge case):** blues, sad, but loud (energy 0.90), valence 0.20
5. **Acoustic Chill Rock (edge case):** rock, but chill, quiet (energy 0.20) and acoustic
6. **Ghost Genre (edge case):** k-pop, a genre that isn't in the catalog
7. **Silent Classical (edge case):** classical, "calm", energy 0.0, valence 1.0

**How I checked the results:**
- I worked out two scores by hand for the Chill Lofi profile and they matched
  the program exactly: Library Rain 8.37 / 8.5 and Storm Runner 1.38 / 8.5.
- I checked that every song's listed reasons add up to its score, for all
  20 songs and all 7 profiles (140 checks, no mismatches).
- The automated tests (`pytest`) pass.

### What surprised me

- **Fuego en la Plaza is in the top 5 for 4 of the 7 profiles,** even though
  it never matches anyone's genre. Its energy (0.86) and positivity (0.88) are
  close to what most upbeat listeners want, so it collects points on sound
  alone.
- **"calm" matches nothing.** It's the name of a mood *family*, not a mood any
  song has, so Silent Classical gets zero mood points from every song.
- **Ghost Genre fails silently.** No song is k-pop, so the best possible score
  drops from 8.5 to 6.0, but the program gives no warning. It just shows
  regular pop songs as if nothing were wrong.

**Intuition check (High-Energy Pop):** Sunrise City at #1 feels right, since it's
upbeat, high-energy pop. Rooftop Lights at #2 also fits. Gym Hero at #3 feels
slightly off: it's pop, but "intense" is more workout music than happy music.
Island Slowdown at #4 feels wrong. It's a slow reggae song (energy 0.55) that
only got in because "carefree" counts as related to "happy." Fuego en la Plaza
(#5) actually sounds more like what this listener wants (energy 0.86, valence
0.88), so I'd swap #4 and #5.

### Profile comparisons

**High-Energy Pop vs Chill Lofi:** the two top-5 lists share no songs. The pop
list is loud and electronic (energy 0.55–0.93), and the lofi list is quiet and
acoustic (energy 0.28–0.42). This makes sense because the two listeners want
opposite things on almost every setting: energy 0.80 vs 0.40, and electronic
vs acoustic.

**High-Energy Pop vs Deep Intense Rock:** both lists include Gym Hero and Fuego
en la Plaza, but Gym Hero moves up from #3 to #2 for the rock fan. This makes
sense because both listeners want loud, electronic music. Gym Hero loses its pop
genre points with the rock fan, but it wins them back with a mood match
("intense", +2.0).

**Chill Lofi vs Deep Intense Rock:** both #1 songs are near-perfect (8.37 and
8.33), but the rock fan's #2 drops to 4.72, while the lofi fan's #5 still
scores 5.97. This makes sense because the catalog has 3 lofi songs plus 2
related genres (jazz and ambient), but only 1 rock song plus 1 related genre
(metal). The lofi fan simply has more good options.

**Sad Banger vs Acoustic Chill Rock:** in Sad Banger the labels win: Rust in
the Rain is #1 (6.13) even though it's quiet (energy 0.33 vs 0.90 wanted). In
Acoustic Chill Rock the sound wins: the only rock song, Storm Runner, ends up
#6 (3.80) and the top 5 has no rock at all. Both follow the same rule.
Whichever side agrees with itself wins: Rust in the Rain matches both genre and
mood, while Storm Runner matches the genre but is loud and electronic when the
listener wants quiet and acoustic.

**High-Energy Pop vs Ghost Genre:** these profiles are the same except for the
genre (pop vs k-pop). The top 2 are the same songs, but each loses its genre
points (Sunrise City 8.37 → 5.87, Rooftop Lights 7.04 → 5.79), and Gym Hero
drops from #3 to #5 (6.07 → 3.57). This makes sense because genre was Gym
Hero's only matching label. Without it, the happy songs lead and Gym Hero has
to compete on sound alone.

**Deep Intense Rock vs Acoustic Chill Rock:** both fans picked rock, but Storm
Runner goes from #1 (8.33) to #6 (3.80), and the two top-5 lists share no songs.
This makes sense because genre is worth only 2.5 points, and every other
preference flipped (energy 0.90 → 0.20, intense → chill, electronic →
acoustic), so Storm Runner fails all of them.

**Chill Lofi vs Silent Classical:** both want quiet, acoustic music, and two
songs appear in both lists (Spacewalk Thoughts and Coffee Shop Stories). But
the lofi #1 scores 8.37, while the classical #1 scores only 2.97. This makes
sense because Silent Classical asks for things the catalog doesn't have: no
song is quieter than 0.28 or happier than 0.88, and "calm" matches no mood. The
only classical song (Tempest Overture) is loud and dramatic, but it wins on
genre points alone.

### Why does "Gym Hero" keep showing up?

Gym Hero shows up for High-Energy Pop (#3), Deep Intense Rock (#2) and Ghost
Genre (#5) because it's a little bit of everything: it's labeled pop, its mood
is "intense", it's very energetic (0.93), fairly upbeat (0.77) and almost fully
electronic. Each listener finds a different reason to like it. The pop fan
gives it genre points, the rock fan gives it mood points, and all three give it
strong energy points (1.62–1.98 out of 2.0). The system
also never takes points *away*. A happy-pop listener doesn't want workout music,
but the "intense" mood just earns zero instead of counting against the song. So
a gym song can still land in a "Happy Pop" list, and with only 2 pop songs in
the catalog there isn't much competition to push it out.

### Weight-shift experiment

I tried doubling the energy weight (2.0 → 4.0) and halving the genre weight
(2.5 → 1.25, related genres 1.25 → 0.625), then put the weights back. Sad
Banger improved, with the loud, dark Ironclad Fury moving to #1 (5.73 / 9.25),
and the #1 song for the three normal profiles didn't change. But songs that
match no labels at all (Storm Runner, Gym Hero, Concrete Psalms) moved into
top-5 lists on energy alone, and the one classical song lost #1. So the results
were more *different* than more *accurate*: the system went from "labels
decide" to "energy decides".

---

## 7. Intended Use and Non-Intended Use

**Intended use:**
- Classroom exploration of how content-based recommenders work.
- Experimenting with the weights and seeing how the rankings change.
- Explaining recommendations, since every score comes with its reasons.

**Not intended for:**
- Real users or real music catalogs.
- Making decisions about artists, like who gets promoted.
- Listeners whose taste can't be described as one genre and one mood.
- Anything that needs listening history or fairness guarantees.

---

## 8. Ideas for Improvement

- **Add a diversity rule to the ranking step** (for example, at most one song
  per artist in the top 5). This would break up filter bubbles, like the same
  LoRoom songs or the same few songs filling every list.
- **Let listeners pick several favorite genres with weights, plus dislikes.**
  This would fix the "rock fan gets no rock" problem, because a listener could
  say rock matters more than mood, and dislikes could push out songs from
  genres they never want.
- **Warn the user when their genre or mood isn't in the catalog.** Right now
  "k-pop" or "calm" just matches nothing, and the user never finds out why the
  results look off.

---

## 9. Personal Reflection

**Biggest learning moment:** Running the edge-case profiles. I expected the
system to break on weird inputs, but it didn't crash. It just quietly gave bad
answers. A "rock fan" who also wanted chill, acoustic music got zero rock songs,
and a "sad banger" listener got a quiet blues song as their #1. That's when I
understood that a recommender is just weights, and the weights decide whose
preferences win. Label points and sound points were almost equal in my design,
so whichever group agreed with itself took over.

**How AI helped, and when I had to double-check it:** AI helped me analyze the
dataset (it found that energy, tempo, and acousticness were nearly the same
signal), test weight options before writing code, and suggest edge-case
profiles I wouldn't have thought of. But I had to check its work. It caught
my own typo (`target_valence: 40` instead of `0.40`), and I caught it giving
two different acousticness rules in my README. My first "rock" profile also
contradicted itself, and I only noticed because the AI's predicted scores
looked wrong. I verified the scoring by doing two songs by hand (Library Rain
8.37, Storm Runner 1.38) and confirming the code matched exactly.

**What surprised me:** How much a few simple rules feel like a real
recommendation. Five "if this matches, add points" checks and a sort produced
lists that mostly felt right, like all-calm songs for a study playlist. It also
surprised me how one song, Fuego en la Plaza, kept showing up for very
different listeners, just because it's high-energy and happy and the catalog
is small.

**What I'd try next:** Add an artist/genre diversity rule so the top 5 aren't
dominated by one style, let users list several genres and dislikes, and test
with a much bigger, more balanced catalog to see whether the biases I found
shrink or just change shape.