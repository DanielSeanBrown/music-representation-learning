import numpy as np

def estimate_key(chroma: np.ndarray) -> tuple[str, list[float, float], float]:
    """Given a 12D chroma vector, estimate the key and return cyclical key encoding.
    A simple implementation of the Krumhansl-Schmuckler key-finding algorithm.
    
    Args:
        chroma (np.ndarray): 12D chroma vector representing the pitch class distribution.

    Returns:
        tuple[str, list[float, float], float]: Estimated key, cyclical key encoding, and key strength.
    """

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


    # Extract pitch class from key string
    key_name = best_key.split()[0]

    key_map = {
        "C": 0,
        "C#": 1,
        "D": 2,
        "D#": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "G": 7,
        "G#": 8,
        "A": 9,
        "A#": 10,
        "B": 11
    }

    key_number = key_map[key_name]

    # cyclical encoding of key (0-11) into 2D vector
    theta = 2 * np.pi * key_number / 12

    key_distance = np.array([
        np.cos(theta),
        np.sin(theta)
    ]).tolist()

    return best_key, key_distance, best_score

def normalise(x: np.ndarray) -> np.ndarray:
    """Normalise a vector to sum to 1."""
    return x / (x.sum() + 1e-9)

def chroma_from_pitches(pitches: np.ndarray) -> np.ndarray:
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
    """Given a song dictionary, extract chroma features and estimate the key.
    Returns a dictionary containing:
        low_chroma      list - 12D chroma vector for low pitches
        mid_chroma      list - 12D chroma vector for mid pitches
        high_chroma     list - 12D chroma vector for high pitches
        total_chroma    list - 12D chroma vector for all pitches
        key             str  - Estimated key of the song
        key_distance    list - Cyclical encoding of the key (2D vector)
        key_strength    float - Strength of the estimated key (correlation score)
    """


    low_chroma = chroma_from_pitches(song["low"]["pitches"])
    mid_chroma = chroma_from_pitches(song["mid"]["pitches"])
    high_chroma = chroma_from_pitches(song["high"]["pitches"])

    total_chroma = normalise(low_chroma + mid_chroma + high_chroma)

    key, key_distance, key_strength = estimate_key(total_chroma)


    return {
        "low_chroma": low_chroma.tolist(),
        "mid_chroma": mid_chroma.tolist(),
        "high_chroma": high_chroma.tolist(),
        "total_chroma": total_chroma.tolist(),
        "key": key,
        "key_distance": key_distance,
        "key_strength": key_strength
    }

if __name__ == "__main__":
    import pandas as pd
    example_song = {
        "low": {"pitches": np.array([60, 62, 64])},
        "mid": {"pitches": np.array([65, 67, 69])},
        "high": {"pitches": np.array([71, 72, 74])}
    }
    example_features = pd.DataFrame([extract_chroma_features(example_song)])
    print(example_features.head())
    print({col: type(example_features[col].iloc[0]) for col in example_features.columns})