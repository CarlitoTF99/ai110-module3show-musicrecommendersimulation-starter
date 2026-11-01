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

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

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
