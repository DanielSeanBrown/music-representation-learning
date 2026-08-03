# Feature Dictionary

This markdown file serves as a reference point for what each feature is, its data type and category.

| Feature Name | Description | Data Type | Category |
|--------------|-------------|-----------|----------|
|note_count      |  Total number of notes in the song.              |  int64| Basic Descriptive|
|mean_pitch      |  Mean pitch of the notes in the song.              |float64| Basic Descriptive|
|std_pitch       |  Standard deviation of the pitches in the song.              |float64| Basic Descriptive|
|pitch_range     |  Range of pitches (max - min) in the song.              |  int64| Basic Descriptive|
|mean_duration   |  Mean duration of the notes in the song.              |float64| Basic Descriptive|
|std_duration    |  Standard deviation of the durations in the song.              |float64| Basic Descriptive|
|mean_velocity   |  Mean velocity of the notes in the song.              |float64| Basic Descriptive|
|std_velocity    |  Standard deviation of the velocities in the song.              |float64| Basic Descriptive|
|num_files       |  Number of files in the song.              |  int64| Basic Descriptive|
|mean_instruments|  Mean number of instruments used across the files in the song.              |float64| Basic Descriptive|
|low_chroma      |  12D normalised chroma vector for low pitches| list | Chroma|
|mid_chroma      |  12D normalised chroma vector for mid pitches| list | Chroma|
|high_chroma     |  12D normalised chroma vector for high pitches| list | Chroma|
|total_chroma    |  12D normalised chroma vector for all pitches| list | Chroma|
|key             |  Estimated key of the song using a simple Krumhansl-Schmuckler-style correlation method| list | Chroma|
|key_distance    |  Cyclical encoding of the key | list | Chroma
|key_strength    |  Strength of the estimated key (correlation score)| list | Chroma|

