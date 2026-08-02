import faiss
import numpy as np
import pandas as pd


def load_data():

    metadata = pd.read_csv(
        "data/processed/metadata_index.csv"
    )

    embeddings = np.load(
        "data/processed/all_features_limit_20_embeddings.npy"
    ).astype("float32")

    index = faiss.read_index(
        "data/processed/all_features_limit_20_index.index"
    )

    return metadata, embeddings, index