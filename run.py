from src.feature_extraction import perform_extraction
from src import download
from src.embeddings import produce_embeddings
from src.config.paths import PROCESSED_DATA_DIR

from pathlib import Path

import pandas as pd
import numpy as np

def main(
        force_download: bool = False,
        force_extraction: bool = False,
        force_embedding: bool = False,
        features_df: pd.DataFrame = None,
        limit: int = 31034):
    """
    Main script for downloading, preprocessing, extracting features, and producing embeddings for the visualisation tool.

    Args:
        force_download (bool): If True, forces re-downloading and preprocessing of MIDI files.
        force_extraction (bool): If True, forces re-extraction of features from MIDI files.
        force_embedding (bool): If True, forces re-production of embeddings from extracted features.
        features_df (pd.DataFrame): Optional pre-extracted features DataFrame. If provided, skips feature extraction.
        limit (int): Maximum number of MIDI files to process. Defaults to 31034 (all available files).
    """

    if limit> 31034:
        print(f"Limit {limit} exceeds the maximum number of available MIDI files (31034). Setting limit to 31034.")
        limit = 31034

    if not Path(PROCESSED_DATA_DIR / "metadata_index.csv").exists() or force_download:
        print("Downloading and preprocessing MIDI files...")
        download.download_and_preprocess_midi_files()

    if not Path(PROCESSED_DATA_DIR / f"simmilarity_features_{limit}.pkl").exists() or force_extraction:
        print("Extracting features from MIDI files...")
        metadata_df = pd.read_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv")
        features_df = perform_extraction(metadata_df, limit=limit, save=True)

    if not Path(PROCESSED_DATA_DIR / f"all_features_limit_{limit}_embeddings.npy").exists() or force_embedding:
        if features_df is None:
            features_df = pd.read_pickle(f"{PROCESSED_DATA_DIR}/simmilarity_features_{limit}.pkl")
        print("Producing embeddings from extracted features...")
        embeddings_df = produce_embeddings(features_df)
        np.save(file=f"{PROCESSED_DATA_DIR}/all_features_limit_{limit}_embeddings", arr=embeddings_df)

    pass


if __name__ == "__main__":

    main(limit = 20)