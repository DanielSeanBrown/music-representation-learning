from loguru import logger
from src.produce_file_index import extract_metadata
from src.evaluation.perform_evaluation import evaluate
from src.feature_extraction import extract_features
from src.download import download_files
from src.embeddings import produce_FAISS_index, produce_embeddings
from src.cleaning import clean_features, reprocess_metadata
from src.config.paths import PROCESSED_DATA_DIR, MSD_METADATA_DIR, LMD_MATCHED_DIR

from pathlib import Path

import pandas as pd
import numpy as np

def main(
        force_download: bool = False,
        force_metadata: bool = False,
        force_extraction: bool = False,
        force_weight_tuning: bool = False,
        force_embedding: bool = False,
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


    if not any((Path(LMD_MATCHED_DIR).exists(), Path(MSD_METADATA_DIR).exists())) or force_download:

        logger.info("Downloading MIDI and h5 metadata files...")
        download_files()

    if not Path(PROCESSED_DATA_DIR / "metadata_index.csv").exists() or force_metadata:

        logger.info("Extracting metadata index from h5 files...")
        extract_metadata()

    if not Path(PROCESSED_DATA_DIR / f"similarity_features_{limit}.parquet").exists() or force_extraction:

        logger.info("Extracting features from MIDI files...")
        extract_features(metadata_df=pd.read_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv"), limit=limit, save=True)

        logger.info("Cleaning extracted features to remove duplicates...")
        clean_features()

        logger.info("Reprocessing metadata to ensure alignment with extracted features...")
        reprocess_metadata() 

    if not Path(PROCESSED_DATA_DIR / f"best_weighting_limit_{limit}.parquet").exists() or force_weight_tuning:
        if Path(PROCESSED_DATA_DIR / "evaluation_table.parquet").exists():

            logger.info("Performing simulated evaluation to determine best weighting for similarity scoring...")
            evaluate(limit=limit, n_trials=20000, save=True, random_seed=19)

        else:
            logger.warning("Evaluation table missing, weight simulation and selection skipped")

    if not Path(PROCESSED_DATA_DIR / f"all_features_limit_{limit}_embeddings.npy").exists() or force_embedding:

        logger.info("Producing embeddings from extracted features...")
        produce_embeddings(limit=limit, save=True) 

    if not Path(PROCESSED_DATA_DIR / f"all_features_limit_{limit}_index.index").exists() or force_embedding:

        logger.info("Producing FAISS index from embeddings...")
        produce_FAISS_index(limit=limit, save=True)

    return


if __name__ == "__main__":

    main(        
        force_download = False,
        force_metadata = False,
        force_extraction = True,
        force_weight_tuning = True,
        force_embedding = True
    )
