import numpy as np

def extract_basic_features(song):

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
    pass