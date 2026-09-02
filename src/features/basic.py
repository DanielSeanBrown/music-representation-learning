import numpy as np

def extract_basic_features(song: dict) -> dict:
    """
    Given a song dictionary containing pitches, durations, velocities, number of files, and instrument counts, this function extracts basic features.
    These include:
        note_count            int64 - Total number of notes in the song.
        mean_pitch          float64 - Mean pitch of the notes in the song.
        std_pitch           float64 - Standard deviation of the pitches in the song.
        pitch_range           int64 - Range of pitches (max - min) in the song.
        mean_duration       float64 - Mean duration of the notes in the song.
        std_duration        float64 - Standard deviation of the durations in the song.
        mean_velocity       float64 - Mean velocity of the notes in the song.
        std_velocity        float64 - Standard deviation of the velocities in the song.
        num_files             int64 - Number of files in the song.
        mean_instruments    float64 - Mean number of instruments used across the files in the song.
    """

    pitches = song["pitches"]
    durations = song["durations"]
    velocities = song["velocities"]

    return {

        "note_count": len(pitches),

        "mean_pitch": np.mean(pitches),
        "std_pitch": np.std(pitches),
        "pitch_range": np.max(pitches) - np.min(pitches),

        "mean_duration": np.mean(durations),
        "std_duration": np.std(durations),

        "mean_velocity": np.mean(velocities),
        "std_velocity": np.std(velocities),

        "num_files": song["num_files"],
        "mean_instruments": np.mean(song["instrument_counts"])
    }

if __name__ == "__main__":
    import pandas as pd
    example_song = {
        "pitches": np.array([60, 62, 64, 65, 67]),
        "durations": np.array([0.5, 0.25, 0.75, 0.5, 1.0]),
        "velocities": np.array([80, 90, 70, 85, 95]),
        "num_files": 5,
        "instrument_counts": np.array([2, 3, 1, 4, 2])
    }
    example = pd.DataFrame([extract_basic_features(example_song)])
    print(example.head())
    print(example.dtypes)
