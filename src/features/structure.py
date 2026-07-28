import numpy as np

def extract_structure_features(song: dict, n_segments: int = 16):
    """Given a song dictionary, extract structural features based on chroma segmentation."""

    starts = song["starts"]
    pitches = song["pitches"]

    if len(starts) < 10: # Not enough notes to segment meaningfully
        return {}

    # Create logarithmically spaced segment edges
    edges = np.linspace(
        starts.min(),
        starts.max(),
        n_segments + 1
    )

    segment_chroma = []

    # For each segment, compute the chroma vector
    for i in range(n_segments):

        mask = (
            (starts >= edges[i]) &
            (starts < edges[i+1])
        )

        seg_pitches = pitches[mask]

        if len(seg_pitches) == 0:
            chroma = np.zeros(12)

        else:
            chroma = np.bincount(seg_pitches % 12, minlength=12)
            chroma = (chroma / (chroma.sum() + 1e-9))

        segment_chroma.append(chroma)

    segment_chroma = np.array(segment_chroma)
    chord_roots = np.argmax(segment_chroma, axis=1) # Identify the most prominent pitch class in each segment
    harmonic_rhythm = np.mean(chord_roots[1:] != chord_roots[:-1]) # Proportion of segments where the chord root changes

    # Calculate the average variation between consecutive segments
    segment_variation = np.mean([
        np.linalg.norm(
            segment_chroma[i]
            - segment_chroma[i+1]
        )
        for i in range(
            len(segment_chroma)-1
        )
    ])

    return {
        "segment_chroma": segment_chroma,
        "chord_progression": chord_roots,
        "harmonic_rhythm": harmonic_rhythm,
        "segment_variation": segment_variation
    }