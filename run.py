import faiss
from loguru import logger

from src.feature_extraction import extract_features
from src import download
from src.embeddings import produce_FAISS_index, produce_embeddings
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
        limit (int): Maximum number of MIDI files to process. Defaults to 31034 (all available files).
    """

    if limit> 31034:
        logger.warning(f"Limit {limit} exceeds the maximum number of available MIDI files (31034). Setting limit to 31034.")
        limit = 31034


    if not Path(PROCESSED_DATA_DIR / "metadata_index.csv").exists() or force_download:
        logger.info("Downloading and preprocessing MIDI files...")
        download.download_and_preprocess_midi_files()

    if not Path(PROCESSED_DATA_DIR / f"simmilarity_features_{limit}.pkl").exists() or force_extraction:
        logger.info("Extracting features from MIDI files...")
        extract_features(metadata_df=pd.read_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv"), limit=limit, save=True)

    if not Path(PROCESSED_DATA_DIR / f"all_features_limit_{limit}_embeddings.npy").exists() or force_embedding:
        logger.info("Producing embeddings from extracted features...")
        produce_embeddings(limit=limit, save=True)

    if not Path(PROCESSED_DATA_DIR / f"all_features_limit_{limit}_index.index").exists() or force_embedding:
        logger.info("Producing FAISS index from embeddings...")
        produce_FAISS_index(limit=limit, save=True)

    pass


if __name__ == "__main__":

    main(force_download=False, force_extraction=True, force_embedding=True, limit=20)
