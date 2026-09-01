import faiss
import numpy as np
import pandas as pd


FEATURE_GROUPS = [
    "stats",
    "chroma",
    "entropy",
    "rhythm",
    "structure",
    "melody",
    "low",
    "mid",
    "high",
]


def load_data():
    """Loads the metadata, weighted embeddings, FAISS index, and unweighted feature groups from the processed data directory.
    This function is used for the fastapi app to load the data for the music explorer.
    
    Returns:
        metadata (pd.DataFrame): The metadata dataframe.
        weighted_embeddings (np.ndarray): The weighted embeddings array.
        index (faiss.Index): The FAISS index.
        unweighted_embeddings (dict): The unweighted feature groups as a dictionary."""

    metadata = pd.read_csv("data/processed/metadata_index_reprocessed.csv")
    weighted_embeddings = np.load("data/processed/all_features_limit_31034_embeddings.npy").astype("float32")
    index = faiss.read_index("data/processed/all_features_limit_31034_index.index")

    loaded = np.load("data/processed/unweighted_features_limit_31034.npz")

    unweighted_embeddings = {
        name:
            loaded[name].astype(
                np.float32,
                copy=False,
            )
        for name in FEATURE_GROUPS
    }



    return (
        metadata,
        weighted_embeddings,
        index,
        unweighted_embeddings
    )