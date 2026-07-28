import numpy as np

def estimate_key(chroma):
    """Given a 12D chroma vector, estimate the key using a simple Krumhansl-Schmuckler-style correlation method."""

    # Define the major and minor key profiles based on Krumhansl & Kessler (1982)
    major_profile = np.array([6.35,2.23,3.48,2.33,4.38,4.09,
                              2.52,5.19,2.39,3.66,2.29,2.88])

    minor_profile = np.array([6.33,2.68,3.52,5.38,2.60,3.53,
                              2.54,4.75,3.98,2.69,3.34,3.17])

    best_score = -1
    best_key = None

    keys = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

    for i in range(12):
        rotated = np.roll(chroma, i)

        major_score = np.corrcoef(rotated, major_profile)[0,1]
        minor_score = np.corrcoef(rotated, minor_profile)[0,1]

        if major_score > best_score:
            best_score = major_score
            best_key = keys[i] + " major"

        if minor_score > best_score:
            best_score = minor_score
            best_key = keys[i] + " minor"

    return best_key, best_score

def normalise(x):
    """Normalise a vector to sum to 1."""
    return x / (x.sum() + 1e-9)

def chroma_from_pitches(pitches):
    """Given a list of pitches, return a 12D chroma vector."""

    if len(pitches) == 0:
        return np.zeros(12)

    return normalise(
        np.bincount(
            pitches.astype(int) % 12,
            minlength=12
        )
    )

def extract_chroma_features(song: dict) -> dict:
    """Given a song dictionary, extract chroma features and estimate the key."""


    low_chroma = chroma_from_pitches(song["low"]["pitches"])
    mid_chroma = chroma_from_pitches(song["mid"]["pitches"])
    high_chroma = chroma_from_pitches(song["high"]["pitches"])

    total_chroma = normalise(low_chroma + mid_chroma + high_chroma)

    key, key_strength = estimate_key(total_chroma)

    return {

        "low_chroma": low_chroma,
        "mid_chroma": mid_chroma,
        "high_chroma": high_chroma,

        "total_chroma": total_chroma,

        "key": key,
        "key_strength": key_strength
    }