from collections import Counter
from pathlib import Path
from collections import defaultdict

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler


import numpy as np
import pandas as pd
from tqdm import tqdm


from src.config.paths import PROCESSED_DATA_DIR
from src.feature_extraction import extract_features_for_song, perform_extraction




def load_dataset(file_name: str) -> pd.DataFrame:
    """
    Load a dataset from a pickle file.

    Args:
        file_name (str): The name of the pickle file to load."""
    
    if not Path(PROCESSED_DATA_DIR / file_name).exists():
        raise FileNotFoundError(f"The file {file_name} does not exist.")
    else:
        return pd.read_pickle(Path(PROCESSED_DATA_DIR / file_name))


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

def produce_embeddings(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce embeddings for the given DataFrame.

    Args:
        features_df (pd.DataFrame): The input DataFrame containing features."""
    

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

    return pd.DataFrame(X, index=features_df.index)




if __name__ == "__main__":
    LIMIT = 15
    if not Path(PROCESSED_DATA_DIR / f"simmilarity_features_{LIMIT}.pkl").exists():
        metadata_df = pd.read_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv")
        features_df = perform_extraction(metadata_df, limit=LIMIT, save=True)
    features_df = load_dataset(f"simmilarity_features_{LIMIT}.pkl")
    embeddings_df = produce_embeddings(features_df)
    np.save(file=f"{PROCESSED_DATA_DIR}/all_features_limit_{LIMIT}_embeddings", arr=embeddings_df)

    print(embeddings_df.head())
