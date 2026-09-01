from scipy.stats import entropy
import numpy as np

def hist_entropy(values: np.ndarray) -> float:
    """Given a list of values, compute the entropy of their histogram."""
    if len(values) == 0:
        return 0
    
    hist, _ = np.histogram(values, bins=20)

    # Normalise 
    hist = (hist /(hist.sum() + 1e-9))

    return entropy(hist)

def extract_entropy_features(song: dict) -> dict:
    """Given a song dictionary, extract entropy-based features for pitch, duration, and inter-onset intervals (IOIs).
    Returns a dictionary containing:
        pitch_entropy      float - Entropy of the pitch distribution
        duration_entropy   float - Entropy of the duration distribution
        ioi_entropy        float - Entropy of the inter-onset interval distribution
    """

    iois = np.diff(np.sort(song["starts"]))

    return {
        "pitch_entropy": hist_entropy(song["pitches"]),
        "duration_entropy":hist_entropy(song["durations"]),
        "ioi_entropy":hist_entropy(iois)
    }

if __name__ == "__main__":
    import pandas as pd
    example_song = {
        "starts": np.array([0.0, 0.5, 1.0, 1.5, 2.0]),
        "pitches": np.array([60, 62, 64, 65, 67]),
        "durations": np.array([0.5, 0.25, 0.75, 0.5, 1.0])
    }
    example = pd.DataFrame([extract_entropy_features(example_song)])
    print(example.head())
    print(example.dtypes)