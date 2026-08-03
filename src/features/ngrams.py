from collections import Counter
import numpy as np

def build_intervals(pitches: np.ndarray) -> np.ndarray:
    """Given a list of pitches, return the intervals between consecutive pitches."""
    if len(pitches) < 2:
        return np.array([])

    return np.diff(pitches)

def build_ngrams(intervals: np.ndarray, n: int = 3) -> Counter:
    """Given a list of intervals, return the n-grams (tuples of length n) and their counts."""
    
    if len(intervals) < n:
        return Counter()

    motifs = [
        tuple(intervals[i:i+n])
        for i in range(
            len(intervals) - n + 1
        )
    ]

    return Counter(motifs)

def extract_ngram_features(song: dict, n: int = 3) -> dict:
    """Given a song dictionary, extract n-gram features based on pitch intervals.
    Returns a dictionary containing:
        melody_intervals  list      - Intervals of the melody
        melody_ngrams     dict      - N-grams of the melody intervals
        low_intervals     list      - Intervals of the low part
        low_ngrams        dict      - N-grams of the low part
        mid_intervals     list      - Intervals of the mid part
        mid_ngrams        dict      - N-grams of the mid part
        high_intervals    list      - Intervals of the high part
        high_ngrams       dict      - N-grams of the high part
    """


    melody_intervals = build_intervals(song["melody"]["pitches"])
    low_intervals = build_intervals(song["low"]["pitches"])
    mid_intervals = build_intervals(song["mid"]["pitches"])
    high_intervals = build_intervals(song["high"]["pitches"])

    return {
        "melody_intervals": melody_intervals.tolist(),
        "melody_ngrams": dict(build_ngrams(melody_intervals, n=n)),
        "low_intervals": low_intervals.tolist(),
        "low_ngrams": dict(build_ngrams(low_intervals, n=n)),
        "mid_intervals": mid_intervals.tolist(),
        "mid_ngrams": dict(build_ngrams(mid_intervals, n=n)),
        "high_intervals": high_intervals.tolist(),
        "high_ngrams": dict(build_ngrams(high_intervals, n=n))
    }

if __name__ == "__main__":
    import pandas as pd
    example_song = {
        "melody": {"pitches": np.array([60, 62, 64, 65, 67])},
        "low": {"pitches": np.array([48, 50, 52])},
        "mid": {"pitches": np.array([55, 57, 59])},
        "high": {"pitches": np.array([72, 74, 76])}
    }
    example = pd.DataFrame([extract_ngram_features(example_song)])
    print(example.head())
    print(example.dtypes)
    print({col: type(example[col].iloc[0]) for col in example.columns})