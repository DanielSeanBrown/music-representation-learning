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

    # ==============================================================
    # METADATA
    # ==============================================================

    metadata = pd.read_csv(
        "data/processed/metadata_index_reprocessed.csv"
    )


    # ==============================================================
    # DEFAULT WEIGHTED EMBEDDINGS
    # ==============================================================

    embeddings = np.load(
        "data/processed/all_features_limit_31034_embeddings.npy"
    ).astype(
        "float32"
    )


    # ==============================================================
    # DEFAULT FAISS INDEX
    # ==============================================================

    index = faiss.read_index(
        "data/processed/all_features_limit_31034_index.index"
    )


    # ==============================================================
    # UNWEIGHTED FEATURE GROUPS
    # ==============================================================

    unweighted_path = (
        "data/processed/unweighted_features_limit_31034.npz"
    )

    loaded = np.load(
        unweighted_path
    )

    unweighted_features = {

        name:
            loaded[name].astype(
                np.float32,
                copy=False,
            )

        for name in FEATURE_GROUPS

        if name in loaded.files

    }




    # ==============================================================
    # RETURN
    # ==============================================================

    return (
        metadata,
        embeddings,
        index,
        unweighted_features,
    )