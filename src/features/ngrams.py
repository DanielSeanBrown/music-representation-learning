from collections import Counter
import numpy as np

def build_intervals(pitches):
    """Given a list of pitches, return the intervals between consecutive pitches."""
    if len(pitches) < 2:
        return np.array([])

    return np.diff(pitches)

def build_ngrams(intervals, n=3):
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

def extract_ngram_features(song, n=3):
    """Given a song dictionary, extract n-gram features based on pitch intervals."""


    melody_intervals = build_intervals(song["melody"]["pitches"])
    low_intervals = build_intervals(song["low"]["pitches"])
    mid_intervals = build_intervals(song["mid"]["pitches"])
    high_intervals = build_intervals(song["high"]["pitches"])

    return {
        "melody_intervals": melody_intervals,
        "melody_ngrams": build_ngrams(melody_intervals, n=n),
        "low_intervals": low_intervals,
        "low_ngrams": build_ngrams(low_intervals, n=n),
        "mid_intervals": mid_intervals,
        "mid_ngrams": build_ngrams(mid_intervals, n=n),
        "high_intervals": high_intervals,
        "high_ngrams": build_ngrams(high_intervals, n=n)
    }