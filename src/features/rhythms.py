import numpy as np

def histogram(values: np.ndarray) -> np.ndarray:
    """Given a list of values, return a normalized histogram with 10 logarithmically spaced bins."""

    if len(values) == 0:
        return np.zeros(10)

    hist = np.histogram(
        values,
        bins=np.logspace(-3, 1, 11)
    )[0]

    return hist / (hist.sum() + 1e-9)

def density(starts: np.ndarray, ends: np.ndarray) -> float:
    """Given a list of note starts and ends, return the density of notes per unit time."""

    if len(starts) < 2:
        return 0

    return len(starts) / (
        ends.max() - starts.min() + 1e-9
    )

def iois(starts: np.ndarray) -> np.ndarray:
    """Given a list of note starts, return the inter-onset intervals."""
    if len(starts) < 2:
        return np.array([])

    return np.diff(np.sort(starts))

def extract_rhythm_features(song: dict) -> dict:
    """Given a song dictionary, extract rhythm features such as inter-onset intervals (IOIs), duration histograms, and density measures.
    Returns a dictionary containing:
        ioi_hist          list - Histogram of inter-onset intervals
        duration_hist     list - Histogram of note durations
        drum_ioi_hist     list - Histogram of drum inter-onset intervals
        bass_ioi_hist     list - Histogram of bass inter-onset intervals
        melody_ioi_hist   list - Histogram of melody inter-onset intervals
        density           float      - Density of notes per unit time
        drum_density      float      - Density of drum notes per unit time
        bass_density      float      - Density of bass notes per unit time
        melody_density    float      - Density of melody notes per unit time
    """

    return {
        "ioi_hist": histogram(iois(song["starts"])).tolist(),
        "duration_hist": histogram(song["durations"]).tolist(),
        "drum_ioi_hist": histogram(iois(song["drums"]["starts"])).tolist(),
        "bass_ioi_hist": histogram(iois(song["low"]["starts"])).tolist(),
        "melody_ioi_hist": histogram(iois(song["melody"]["starts"])).tolist(),
        "density": 
            density(
                song["starts"],
                song["ends"]
            ),
        "drum_density":
            density(
                song["drums"]["starts"],
                song["drums"]["ends"]
            ),
        "bass_density":
            density(
                song["low"]["starts"],
                song["low"]["ends"]
            ),
        "melody_density":
            density(
                song["melody"]["starts"],
                song["melody"]["ends"]
            )
    }

if __name__ == "__main__":
    import pandas as pd
    example_song = {
        "starts": np.array([0.0, 0.5, 1.0, 1.5, 2.0]),
        "ends": np.array([0.5, 1.0, 1.5, 2.0, 2.5]),
        "durations": np.array([0.5, 0.5, 0.5, 0.5, 0.5]),
        "drums": {"starts": np.array([0.0, 1.0]), "ends": np.array([0.5, 1.5])},
        "low": {"starts": np.array([0.5, 1.5]), "ends": np.array([1.0, 2.0])},
        "melody": {"starts": np.array([1.0, 2.0]), "ends": np.array([1.5, 2.5])}
    }
    example = pd.DataFrame([extract_rhythm_features(example_song)])
    print(example.head())
    print({col: type(example[col].iloc[0]) for col in example.columns})