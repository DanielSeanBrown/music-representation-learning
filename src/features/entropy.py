from scipy.stats import entropy
import numpy as np

def hist_entropy(values):
    """Given a list of values, compute the entropy of their histogram."""
    if len(values) == 0:
        return 0
    
    hist, _ = np.histogram(
        values,
        bins=20
    )

    hist = (
        hist /
        (hist.sum() + 1e-9)
    )

    return entropy(hist)

def extract_entropy_features(song: dict) -> dict:
    """Given a song dictionary, extract entropy-based features for pitch, duration, and inter-onset intervals (IOIs)."""

    iois = np.diff(
        np.sort(song["starts"])
    )

    return {
        "pitch_entropy": hist_entropy(song["pitches"]),
        "duration_entropy":hist_entropy(song["durations"]),
        "ioi_entropy":hist_entropy(iois)
    }