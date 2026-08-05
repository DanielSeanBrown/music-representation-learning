from collections import Counter
from pathlib import Path
from collections import defaultdict

import faiss
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler


import numpy as np
import pandas as pd
from tqdm import tqdm

from loguru import logger


from src.config.paths import PROCESSED_DATA_DIR
from src.feature_extraction import extract_features



def vectorise_counter(counter, vocab):

    vec = np.zeros(len(vocab))
    
    total = sum(counter.values())

    if total == 0:
        return vec

    for item, count in counter.items():

        if item in vocab:
            vec[vocab[item]] = count / total

    return vec

def build_embedding(row, ngram_vocab):

    parts = []

    parts.append(row["total_chroma"])
    parts.append(row["low_chroma"])
    parts.append(row["mid_chroma"])
    parts.append(row["high_chroma"])

    parts.append(row["ioi_hist"])
    parts.append(row["duration_hist"])

    parts.append(np.array([
        row["density"],
        row["drum_density"],
        row["bass_density"],
        row["melody_density"]
    ]))

    parts.append(np.array([
        row["pitch_entropy"],
        row["duration_entropy"],
        row["ioi_entropy"]
    ]))

    parts.append(
        vectorise_counter(
            row["melody_ngrams"],
            ngram_vocab
        )
    )

    return np.concatenate(parts)

def produce_embeddings(features_df: pd.DataFrame=None, limit: int = 30, save: bool = True) -> pd.DataFrame:
    """
    Produce embeddings for the given DataFrame.

    Args:
        features_df (pd.DataFrame): The input DataFrame containing features, if left empty, it will be loaded from the pickle file.
        limit (int): The limit for the number of features to consider.
        save (bool): Whether to save the embeddings to a numpy file. Defaults to True."""

    if features_df is None:
        features_df = pd.read_parquet(f"{PROCESSED_DATA_DIR}/simmilarity_features_{limit}.parquet")

    global_vocab = Counter()
    for ngrams in features_df["melody_ngrams"]:
        global_vocab.update(ngrams)

    TOP_NGRAMS = 500
    ngram_vocab = {
        ngram: i
        for i, (ngram, _)
        in enumerate(global_vocab.most_common(TOP_NGRAMS))
    }

    X = np.vstack([
        build_embedding(row, ngram_vocab)
        for _, row in features_df.iterrows()
    ])

    X = StandardScaler().fit_transform(X)

    if save:
        np.save(f"{PROCESSED_DATA_DIR}/all_features_limit_{limit}_embeddings.npy", X)

    return pd.DataFrame(X, index=features_df.index)

def produce_FAISS_index(embeddings: np.ndarray=None, limit: int = 30, save: bool = True) -> "faiss.Index":
    """
    Produce a FAISS index for the given embeddings.

    Args:
        embeddings (np.ndarray): The input embeddings."""
    
    if embeddings is None:
        embeddings = np.load(f"{PROCESSED_DATA_DIR}/all_features_limit_{limit}_embeddings.npy")

    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings) 
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)

    if save:
        faiss.write_index(index, f"{PROCESSED_DATA_DIR}/all_features_limit_{limit}_index.index")

    return index




if __name__ == "__main__":
    LIMIT = 5000
    metadata_df = pd.read_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv")
    if "faiss_id" not in metadata_df.columns:
        metadata_df["faiss_id"] = metadata_df.index
        metadata_df.to_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv", index=False)
    if not Path(PROCESSED_DATA_DIR / f"simmilarity_features_{LIMIT}.parquet").exists():
        features_df = extract_features(metadata_df, limit=LIMIT, save=True)
    features_df = pd.read_parquet(f"{PROCESSED_DATA_DIR}/simmilarity_features_{LIMIT}.parquet")
    embeddings_df = produce_embeddings(features_df, limit=LIMIT, save=True)
    index = produce_FAISS_index(embeddings_df.values, limit=LIMIT, save=True)
    faiss.write_index(index, f"{PROCESSED_DATA_DIR}/all_features_limit_{LIMIT}_index.index")

    logger.info(embeddings_df.head())
