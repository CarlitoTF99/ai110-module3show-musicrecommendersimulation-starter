# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**, a content-based music recommender simulation.

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works

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

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias 

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

---

## 7. Evaluation  

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

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
