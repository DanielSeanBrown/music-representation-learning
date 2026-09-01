from pathlib import Path
from loguru import logger
import pandas as pd
from tqdm import tqdm

from src.config.paths import PROCESSED_DATA_DIR


def clean_features():
    """Clean the extracted features by removing duplicate songs.
    Duplication here refers to a duplicate title and artist combinations and not the track ID."""

    metadata_path = PROCESSED_DATA_DIR / "metadata_index_reprocessed.csv"

    if metadata_path.exists():
        metadata_df = pd.read_csv(metadata_path)
    else:
        reprocess_metadata()
        metadata_df = pd.read_csv(metadata_path)

    metadata_df["_artist_clean"] = metadata_df["artist_name"].fillna("").astype(str).str.strip().str.casefold()
    metadata_df["_title_clean"] = metadata_df["title"].fillna("").astype(str).str.strip().str.casefold()
    
    duplicate_tracks = set(metadata_df.loc[metadata_df[["_title_clean", "_artist_clean"]].duplicated(keep="first"),"track_id"])

    logger.debug(f"Found {len(duplicate_tracks)} duplicate tracks to remove.")

    chunk_paths = list((PROCESSED_DATA_DIR / "full_extraction_parts").glob("similarity_features_*.parquet"))

    for chunk_path in tqdm(chunk_paths, desc="Cleaning features"):
        chunk_df = pd.read_parquet(chunk_path)

        logger.debug(f"Cleaning chunk {chunk_path} with {len(chunk_df)} tracks before removing duplicates.")
        chunk_df = chunk_df[~chunk_df["track_id"].isin(duplicate_tracks)]

        logger.debug(f"Cleaning chunk {chunk_path} with {len(chunk_df)} tracks after removing duplicates.")
        chunk_df.to_parquet(chunk_path, index=False)


def reprocess_metadata():
    """
    Reprocess the metadata to ensure it lines up correctly with the extracted features. 
    This function reads the existing metadata, processes it, and saves it back.
    """
    metadata_path = PROCESSED_DATA_DIR / "metadata_index.csv"
    reprocessed_metadata_path = PROCESSED_DATA_DIR / "metadata_index_reprocessed.csv"
    
    if not metadata_path.exists():
        logger.error(f"Metadata file {metadata_path} does not exist.")
        return
    
    found_tracks = set()
    chunk_paths = list((PROCESSED_DATA_DIR / "full_extraction_parts").glob("similarity_features_*.parquet"))
    for chunk_path in tqdm(chunk_paths, desc="Reprocessing metadata"):
        chunk_df = pd.read_parquet(chunk_path)
        found_tracks.update(chunk_df["track_id"].tolist())

    metadata_df = pd.read_csv(metadata_path)
    original_count = len(metadata_df)
    
    # Filter the metadata to include only found tracks
    metadata_df = metadata_df[metadata_df["track_id"].isin(found_tracks)]
    logger.info(f"Reprocessed showed {original_count - len(metadata_df)} entries were missed during extraction.")

    # Create FAISS index for the reprocessed metadata
    metadata_df["faiss_id"] = range(len(metadata_df))

    # Save the processed metadata back to the same file
    metadata_df.to_csv(reprocessed_metadata_path, index=False)
    logger.info(f"Reprocessed metadata saved to {reprocessed_metadata_path}.")

if __name__ == "__main__":
    clean_features()
    reprocess_metadata()