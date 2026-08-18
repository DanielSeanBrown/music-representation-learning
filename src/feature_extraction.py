import pretty_midi
import numpy as np
from pathlib import Path
from collections import defaultdict

import pandas as pd
from tqdm import tqdm
from loguru import logger

from src.config.paths import PROCESSED_DATA_DIR
from src.features.basic import extract_basic_features
from src.features.chroma import extract_chroma_features
from src.features.ngrams import extract_ngram_features
from src.features.rhythms import extract_rhythm_features
from src.features.structure import extract_structure_features
from src.features.entropy import extract_entropy_features

def load_song_data(midi_path: str, LOW_MAX:int = 48, MID_MAX:int = 72) -> dict:
    """Load and preprocess MIDI files from a given directory.
    
    Args:
        midi_path (str): Path to the directory containing MIDI files.
        LOW_MAX (int): Maximum pitch for low notes.
        MID_MAX (int): Maximum pitch for mid notes.

    Returns:
        dict: A dictionary containing the extracted song data.
    """

    midi_path = Path(midi_path)
    midi_files = list(midi_path.glob("*.mid"))

    if not midi_files:
        return None

    all_notes = []

    low_notes = []
    mid_notes = []
    high_notes = []

    drum_notes = []

    instrument_programs = []
    instrument_counts = []


    for file in midi_files:

        try:
            midi = pretty_midi.PrettyMIDI(str(file))
        except Exception:
            continue

        instrument_counts.append(len(midi.instruments))

        for instrument in midi.instruments:

            instrument_programs.append(instrument.program)

            target = drum_notes if instrument.is_drum else None

            for note in instrument.notes:

                note_tuple = (
                    note.start,
                    note.end,
                    note.pitch,
                    note.velocity
                )

                if instrument.is_drum:
                    drum_notes.append(note_tuple)
                    continue

                all_notes.append(note_tuple)

                if note.pitch < LOW_MAX:
                    low_notes.append(note_tuple)

                elif note.pitch < MID_MAX:
                    mid_notes.append(note_tuple)

                else:
                    high_notes.append(note_tuple)

    if len(all_notes) < 5:
        return None

    # Sort everything by onset
    all_notes.sort(key=lambda x: x[0])
    low_notes.sort(key=lambda x: x[0])
    mid_notes.sort(key=lambda x: x[0])
    high_notes.sort(key=lambda x: x[0])
    drum_notes.sort(key=lambda x: x[0])

    # --------------------------------------------------
    # Melody extraction
    # Highest note at each onset
    # --------------------------------------------------

    by_time = defaultdict(list)

    for start, end, pitch, velocity in all_notes:
        by_time[start].append(
            (pitch, end, velocity)
        )

    melody_notes = []

    for start, notes in by_time.items():

        pitch, end, velocity = max(
            notes,
            key=lambda x: x[0]
        )

        melody_notes.append(
            (start, end, pitch, velocity)
        )

    melody_notes.sort(key=lambda x: x[0])

    # --------------------------------------------------
    # Helper
    # --------------------------------------------------

    def unpack(notes):

        if len(notes) == 0:
            return {
                "starts": np.array([]),
                "ends": np.array([]),
                "pitches": np.array([]),
                "velocities": np.array([]),
                "durations": np.array([])
            }

        starts = np.array([n[0] for n in notes])
        ends = np.array([n[1] for n in notes])

        return {
            "starts": starts,
            "ends": ends,
            "pitches": np.array([n[2] for n in notes]),
            "velocities": np.array([n[3] for n in notes]),
            "durations": ends - starts
        }

    return {
        "path": str(midi_path),
        "num_files": len(midi_files),
        "instrument_counts": instrument_counts,
        "instrument_programs": instrument_programs,
        "notes": all_notes,
        "low_notes": low_notes,
        "mid_notes": mid_notes,
        "high_notes": high_notes,
        "drum_notes": drum_notes,
        "melody_notes": melody_notes,
        **unpack(all_notes),
        "low": unpack(low_notes),
        "mid": unpack(mid_notes),
        "high": unpack(high_notes),
        "drums": unpack(drum_notes),
        "melody": unpack(melody_notes)
    }

def perform_extraction_for_file(midi_path: str) -> dict:
    """Given the path to a directory containing MIDI files, extract a comprehensive set of musical features."""

    song = load_song_data(midi_path) # Perform preprocessing of song data

    if song is None:
        return None

    return {
        **extract_basic_features(song),
        **extract_chroma_features(song),
        **extract_ngram_features(song),
        **extract_rhythm_features(song),
        **extract_structure_features(song),
        **extract_entropy_features(song),
    }

def extract_full_in_chunks(metadata_df: pd.DataFrame, extraction_func: callable=perform_extraction_for_file, chunk_size: int = 4000) -> pd.DataFrame:
    """Extract features in chunks for large datasets to avoid memory issues.

    Args:
        metadata_df (pd.DataFrame): DataFrame containing metadata about the MIDI files, including paths.
        extraction_func (callable): Function that takes a MIDI file path and returns a dictionary of extracted features.
        chunk_size (int, optional): Number of rows to process in each chunk. Defaults to 4000.

    Returns:
        pd.DataFrame: DataFrame containing all extracted features.
    """

    all_rows = []

    for start_idx in range(0, metadata_df.shape[0], chunk_size):
        end_idx = min(start_idx + chunk_size, metadata_df.shape[0])
        logger.info(f"Processing rows {start_idx} to {end_idx}...")
        part_metadata_df = metadata_df.iloc[start_idx:end_idx]

        part_rows = []
        for idx, row in tqdm(part_metadata_df.iterrows(), total=part_metadata_df.shape[0], desc=f"Extracting features from MIDI files (rows {start_idx} to {end_idx})"):
            features = extraction_func(row["midi_path"])
            if features is not None:
                features["track_id"] = row["track_id"]
                features["artist"] = row["artist_name"]
                features["title"] = row["title"]
                part_rows.append(features)

        part_df = pd.DataFrame(part_rows)
        if not part_df.empty:
            part_df.to_parquet(f"{PROCESSED_DATA_DIR}/full_extraction_parts/similarity_features_part_{start_idx}_{end_idx}.parquet", index=False)
        all_rows.extend(part_rows)

    return pd.DataFrame(all_rows)


def extract_features(metadata_df: pd.DataFrame, extraction_func: callable=perform_extraction_for_file, limit: int = 10, save: bool = True) -> pd.DataFrame:

    """Extract features using the provided function for MIDI files listed in the metadata DataFrame. 

    If the limit is equal to the full size of the dataset, then extraction is performed in parts.

    Args:
        metadata_df (pd.DataFrame): DataFrame containing metadata about the MIDI files, including paths.
        extraction_func (callable): Function that takes a MIDI file path and returns a dictionary of extracted features.
        limit (int, optional): Maximum number of rows to process for testing. Defaults to 10.
        save (bool, optional): Whether to save the extracted features to a pickle file. Defaults to True.
        
    Returns:
        pd.DataFrame: DataFrame containing the extracted features.
    """

    rows = []

    # Ensure limit cannot exceed the total number of available MIDI files
    if limit > 31034:
        limit = 31034
    
    if limit == 31034:
        logger.info("Extracting features in parts due to large dataset size...")
        return extract_full_in_chunks(metadata_df, extraction_func=extraction_func, chunk_size=4000)
    
    for idx, row in tqdm(metadata_df.iterrows(), total=metadata_df.shape[0], desc="Extracting features from MIDI files"):

        if idx < limit:  # Process only the first `limit` rows 
            features = extraction_func(row["midi_path"])
        
            if features is not None:
                features["track_id"] = row["track_id"]
                features["artist"] = row["artist_name"]
                features["title"] = row["title"]
                rows.append(features)
    features_df = pd.DataFrame(rows)
    if save:
        features_df.to_parquet(f"{PROCESSED_DATA_DIR}/similarity_features_{limit}.parquet", index=False)

    return pd.DataFrame(rows)

if __name__ == "__main__":

    # Check if the metadata file exists
    if not Path(PROCESSED_DATA_DIR / "metadata_index.csv").exists():
        logger.error(f"Metadata file not found at {PROCESSED_DATA_DIR}/metadata_index.csv. Please ensure the metadata file exists before running feature extraction.")
        exit(1)

    metadata_df = pd.read_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv")
    logger.info("Extracting features for the first 30 rows of metadata...")
    features_df = extract_features(metadata_df, limit=30, save=True)
    logger.info(features_df.head())
    for col in features_df.columns:
        logger.info(f"Column: {col}, Type: {type(features_df[col].iloc[0])}")