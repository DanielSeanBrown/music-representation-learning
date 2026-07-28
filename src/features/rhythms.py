import numpy as np

def histogram(values):
    """Given a list of values, return a normalized histogram with 10 logarithmically spaced bins."""

    if len(values) == 0:
        return np.zeros(10)

    hist = np.histogram(
        values,
        bins=np.logspace(-3, 1, 11)
    )[0]

    return hist / (hist.sum() + 1e-9)

def density(starts, ends):
    """Given a list of note starts and ends, return the density of notes per unit time."""

    if len(starts) < 2:
        return 0

    return len(starts) / (
        ends.max() - starts.min() + 1e-9
    )

def iois(starts):
    """Given a list of note starts, return the inter-onset intervals."""
    if len(starts) < 2:
        return np.array([])

    return np.diff(np.sort(starts))

def extract_rhythm_features(song: dict) -> dict:
    """Given a song dictionary, extract rhythm features such as inter-onset intervals (IOIs), duration histograms, and density measures."""

    return {
        "ioi_hist": histogram(iois(song["starts"])),
        "duration_hist": histogram(song["durations"]),
        "drum_ioi_hist": histogram(iois(song["drums"]["starts"])),
        "bass_ioi_hist": histogram(iois(song["low"]["starts"])),
        "melody_ioi_hist": histogram(iois(song["melody"]["starts"])),
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