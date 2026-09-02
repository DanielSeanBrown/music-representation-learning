from collections import Counter
from pathlib import Path

import faiss
import json
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

from src.config.paths import PROCESSED_DATA_DIR
from src.feature_extraction import extract_features




def process_ngrams(features_df: pd.DataFrame, col: str, top_n: int = 500,) -> dict:
    """
    Build a vocabulary containing the most common n-grams
    Args:
        features_df (pd.DataFrame): DataFrame containing the features.
        col (str): Column name containing the n-grams.
        top_n (int): Number of top n-grams to include in the vocabulary.
    Returns:
        dict: Vocabulary mapping n-grams to indices.
    """

    counts = Counter()

    for ngrams in features_df[col]:
        ngrams = json.loads(ngrams)
        counts.update(ngrams.keys())

    vocab = {
        ngram: i
        for i, (ngram, _) in enumerate(
            counts.most_common(top_n)
        )
    }

    return vocab


def vectorise_counter(counter, vocab: dict) -> np.ndarray:
    """
    Convert an n-gram Counter into a normalised vector.
    Args:
        counter (Counter): Counter containing n-grams and their counts.
        vocab (dict): Vocabulary mapping n-grams to indices.
    Returns:
        np.ndarray: Normalised vector representation of the n-grams.
    """

    vec = np.zeros(
        len(vocab),
        dtype=np.float32,
    )

    total = sum(counter.values())

    if total == 0:
        return vec

    for item, count in counter.items():

        if item in vocab:
            vec[vocab[item]] = count / total

    return vec


def build_feature_groups(row: pd.Series, ngram_vocab: dict, low_vocab: dict ,mid_vocab: dict, high_vocab: dict,) -> dict:
    """
    Extract the different feature groups from one song.

    No standardisation or weighting happens here.

    Args:
        row (pd.Series): A row from the features DataFrame.
        ngram_vocab (dict): Vocabulary for melody n-grams.
        low_vocab (dict): Vocabulary for low register n-grams.
        mid_vocab (dict): Vocabulary for mid register n-grams.
        high_vocab (dict): Vocabulary for high register n-grams.

    Returns:
        Dictionary containing one numpy array per feature group.
    """

    stats = np.array([
        row["note_count"],
        row["mean_pitch"],
        row["std_pitch"],
        row["pitch_range"],
        row["mean_duration"],
        row["std_duration"],
        row["mean_velocity"],
        row["std_velocity"],
        row["mean_instruments"]
    ], dtype=np.float32)

    chroma = np.concatenate([
        np.asarray(json.loads(row["total_chroma"]),dtype=np.float32),
        np.asarray(json.loads(row["low_chroma"]),dtype=np.float32),
        np.asarray(json.loads(row["mid_chroma"]),dtype=np.float32),
        np.asarray(json.loads(row["high_chroma"]),dtype=np.float32),
        np.asarray([row["key_strength"]],dtype=np.float32),
        np.asarray(json.loads(row["key_distance"]),dtype=np.float32),
    ])

    entropy = np.array([
        row["pitch_entropy"],
        row["duration_entropy"],
        row["ioi_entropy"]
    ], dtype=np.float32)


    rhythm = np.concatenate([
        np.asarray( json.loads(row["ioi_hist"]), dtype=np.float32),
        np.asarray( json.loads(row["duration_hist"]), dtype=np.float32),
        np.asarray( json.loads(row["drum_ioi_hist"]), dtype=np.float32),
        np.asarray( json.loads(row["bass_ioi_hist"]), dtype=np.float32),
        np.asarray(json.loads(row["melody_ioi_hist"]), dtype=np.float32),
        np.asarray([row["density"]],dtype=np.float32),
        np.asarray([row["drum_density"]],dtype=np.float32),
        np.asarray([row["bass_density"]],dtype=np.float32,),
        np.asarray([row["melody_density"]],dtype=np.float32,),
    ])


    structure = np.concatenate([
        np.asarray(json.loads(row["segment_chroma"]),dtype=np.float32).flatten(),
        np.asarray(json.loads(row["chord_progression"]),dtype=np.float32),
        np.asarray([row["harmonic_rhythm"]],dtype=np.float32),
        np.asarray([row["segment_variation"]],dtype=np.float32),
    ])


    melody = vectorise_counter(json.loads(row["melody_ngrams"]),ngram_vocab)
    low = vectorise_counter(json.loads(row["low_ngrams"]),low_vocab)
    mid = vectorise_counter(json.loads(row["mid_ngrams"]),mid_vocab)
    high = vectorise_counter(json.loads(row["high_ngrams"]),high_vocab)


    return {
        "stats": stats,
        "chroma": chroma,
        "entropy": entropy,
        "rhythm": rhythm,
        "structure": structure,
        "melody": melody,
        "low": low,
        "mid": mid,
        "high": high,
    }


def build_feature_matrices(
    features_df: pd.DataFrame,
    melody_vocab: dict,
    low_vocab: dict,
    mid_vocab: dict,
    high_vocab: dict,
) -> dict:
    """
    Build one matrix per feature group.


    Each matrix has shape:

        n_songs x n_features

    """

    groups = []

    for _, row in tqdm(
        features_df.iterrows(),
        total=len(features_df),
        desc="Building feature groups",
    ):
        groups.append(
            build_feature_groups(row,melody_vocab,low_vocab,mid_vocab,high_vocab)
        )


    feature_names = [
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

    feature_matrices = {}

    for name in feature_names:

        feature_matrices[name] = np.vstack([
            group[name]
            for group in groups
        ]).astype(np.float32,copy=False)

        logger.debug(
            f"{name}: "
            f"{feature_matrices[name].shape}"
        )

    return feature_matrices



def standardise_feature_groups(
    feature_matrices: dict,
    standardise_chroma: bool = False,
):
    """
    Standardise each feature dimension across songs.

    For example, if mid has shape:

        1000 x 300

    each of the 300 dimensions is standardised independently
    across the 1000 songs.

    Chroma is left untouched by default because the chroma
    vectors are already normalised.

    Args:
        feature_matrices (dict): Dictionary containing one matrix per feature group.
        standardise_chroma (bool): Whether to standardise the chroma feature group. Defaults to False.

    Returns:
        feature_matrices (dict): Dictionary containing the standardised feature matrices.
    """

    for name, matrix in feature_matrices.items():

        if name == "chroma" and not standardise_chroma:
            continue

        scaler = StandardScaler()

        feature_matrices[name] = scaler.fit_transform(matrix).astype(np.float32,copy=False)

    return feature_matrices


def apply_weights(
    feature_matrices: dict,
    weights: dict,
) -> dict:
    """
    Apply one weight to each feature group.

    Note: Weights are applied after standardisation. This was a source of errors in the past

    returns a new dictionary with the weighted feature matrices.
    """

    weighted = {}

    for name, matrix in feature_matrices.items():

        weight = weights.get(name,1.0)

        weighted[name] = (matrix * weight).astype(np.float32,copy=False)

        logger.debug(f"{name} weight = {weight}")

    return weighted



def combine_feature_groups(
    feature_matrices: dict,
) -> np.ndarray:
    """
    Concatenate all feature groups into one embedding matrix.

    Args:
        feature_matrices (dict): Dictionary containing one matrix per feature group.
    Returns:
        X (np.ndarray): Concatenated embedding matrix of shape (n_songs, n_features).
    """

    feature_order = [
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

    X = np.concatenate(
        [feature_matrices[name]for name in feature_order],axis=1,
    )

    # Explicitly guarantee C-contiguous float32 memory.
    # This is important for FAISS, which expects C-contiguous arrays. Errors were encountered in the past when this was not done rigorously.
    X = np.array(X,dtype=np.float32,order="C",copy=True)

    logger.info(f"Final embedding matrix: {X.shape}")
    logger.debug(f"C-contiguous: "f"{X.flags['C_CONTIGUOUS']}")
    logger.debug(f"dtype: {X.dtype}")

    return X

def produce_embeddings_from_chunks():
    """
    Produce embeddings from multiple parquet files.

    This is used for full extraction.
    """

    logger.info("Producing embeddings from chunks...")

    feature_matrices = {
        "stats": [],
        "chroma": [],
        "entropy": [],
        "rhythm": [],
        "structure": [],
        "melody": [],
        "low": [],
        "mid": [],
        "high": [],
    }

    chunks = list((PROCESSED_DATA_DIR / "full_extraction_parts").glob("similarity_features_*.parquet"))
    chunks.sort(key=lambda p: int(p.stem.split("_")[-2]))

    ngram_df = pd.DataFrame()
    for chunk_path in tqdm(chunks, desc="Building n-gram vocabularies"):
        chunk_df = pd.read_parquet(chunk_path)
        ngram_df = pd.concat([ngram_df, chunk_df[["melody_ngrams", "low_ngrams", "mid_ngrams", "high_ngrams"]]], ignore_index=True)

    melody_vocab = process_ngrams(ngram_df,col="melody_ngrams",top_n=500)
    low_vocab = process_ngrams(ngram_df,col="low_ngrams",top_n=300)
    mid_vocab = process_ngrams(ngram_df,col="mid_ngrams",top_n=300)
    high_vocab = process_ngrams(ngram_df,col="high_ngrams",top_n=300)

    for chunk_path in chunks:

        logger.info(f"Processing chunk: {chunk_path.name}")

        features_df = pd.read_parquet(chunk_path)

        chunk_feature_matrices = build_feature_matrices(
            features_df,
            melody_vocab,
            low_vocab,
            mid_vocab,
            high_vocab,
        )

        for name in feature_matrices.keys():
            feature_matrices[name].append(chunk_feature_matrices[name])

    # Concatenate all chunks
    for name in feature_matrices.keys():
        feature_matrices[name] = np.vstack(feature_matrices[name]).astype(np.float32,copy=False)

    return feature_matrices

def extract_embeddings_from_single_file(
    features_df: pd.DataFrame = None,
    limit: int = 30,
) -> pd.DataFrame:
    """
    Produce weighted embeddings from a single parquet file.

    Args:
        features_df (pd.DataFrame): DataFrame containing the features. If None, it will be loaded from the parquet file.
        limit (int): Limit for the number of features to consider. Defaults to 30.
        weights (dict): Dictionary containing the weights for each feature group. If None, default weights will be used.
        save (bool): Whether to save the embeddings to a numpy file. Defaults to True.
        save_unweighted (bool): Whether to save the unweighted embeddings to a numpy file. Defaults to False.
        """
    
    logger.info("Producing embeddings...")

    if features_df is None:
            features_df = pd.read_parquet(PROCESSED_DATA_DIR /f"similarity_features_{limit}.parquet")
    
    
    melody_vocab = process_ngrams(features_df,col="melody_ngrams",top_n=500)
    low_vocab = process_ngrams(features_df,col="low_ngrams",top_n=300)
    mid_vocab = process_ngrams(features_df,col="mid_ngrams",top_n=300)
    high_vocab = process_ngrams(features_df,col="high_ngrams",top_n=300)

    feature_matrices = build_feature_matrices(features_df,melody_vocab,low_vocab,mid_vocab,high_vocab,)
    return feature_matrices


def produce_embeddings(
    features_df: pd.DataFrame = None,
    limit: int = 30,
    weights: dict = None,
    save: bool = True,
    save_unweighted = True
) -> pd.DataFrame:
    """
    Produce weighted embeddings.

    Args:
        features_df (pd.DataFrame): DataFrame containing the features. If None, it will be loaded from the parquet file.
        limit (int): Limit for the number of features to consider. Defaults to 30. 
        weights (dict): Dictionary containing the weights for each feature group. If None, default weights will be used.
        save (bool): Whether to save the embeddings to a numpy file. Defaults to True.
        save_unweighted (bool): Weather to save the unweighted embeddings to a numpy file. Defaults to True.
    
    Returns:
        embeddings_df (pd.DataFrame): DataFrame containing the embeddings,

    Steps:
        1. Load features from parquet if not provided.
        2. Build vocabularies for melody, low, mid, and high n-grams.
        3. Build feature matrices for each feature group.
        4. Standardise each feature group.
        5. Apply weights to each feature group.
        6. Concatenate all feature groups into one embedding matrix.
    """


    if weights is None:
        if (PROCESSED_DATA_DIR / "best_weighting_limit_31034.parquet").exists():
            logger.info("Loading best weighting from previous evaluation...")
            best_weighting_df = pd.read_parquet(PROCESSED_DATA_DIR / "best_weighting_limit_31034.parquet")
            best_weighting = best_weighting_df.loc[0, [col for col in best_weighting_df.columns if "weight" in col]].to_dict()
            weights = best_weighting
        else:
            logger.warning("Weight evaluation results not found. Using default weights.")
            weights = {
                "stats": 1.0,
                "chroma": 1.0,
                "entropy": 1.0,
                "rhythm": 1.0,
                "structure": 1.0,
                "melody": 1.0,
                "low": 1.0,
                "mid": 1.0,
                "high": 1.0
            }

    if limit == 31034:
        feature_matrices = produce_embeddings_from_chunks()

    else:
        feature_matrices = extract_embeddings_from_single_file(features_df, limit)

    
    feature_matrices = standardise_feature_groups(feature_matrices, standardise_chroma=False)

    if save_unweighted:
        np.savez(
            PROCESSED_DATA_DIR / f"unweighted_features_limit_{limit}.npz",
            stats=feature_matrices["stats"],
            chroma=feature_matrices["chroma"],
            entropy=feature_matrices["entropy"],
            rhythm=feature_matrices["rhythm"],
            structure=feature_matrices["structure"],
            melody=feature_matrices["melody"],
            low=feature_matrices["low"],
            mid=feature_matrices["mid"],
            high=feature_matrices["high"],
        )

    feature_matrices = apply_weights(feature_matrices,weights)

    X = combine_feature_groups(feature_matrices)
    faiss.normalize_L2(X)

    if save:
        np.save(PROCESSED_DATA_DIR /f"all_features_limit_{limit}_embeddings.npy",X)

    metadata_df = pd.read_csv(PROCESSED_DATA_DIR / "metadata_index_reprocessed.csv")

    if limit == 31034:
        return pd.DataFrame(X,index=metadata_df.index)
    else:
        return pd.DataFrame(X,index=metadata_df.iloc[:len(X)].index)


def produce_FAISS_index(
    embeddings: np.ndarray = None,
    limit: int = 30,
    save: bool = True,
):
    """
    Produce a FAISS cosine-similarity index.

    IndexFlatIP + L2-normalisation gives cosine similarity.
    """

    logger.info("Producing FAISS index")

    if embeddings is None:
        embeddings = np.load(PROCESSED_DATA_DIR /f"all_features_limit_{limit}_embeddings.npy")


    embeddings = np.array(
        embeddings,
        dtype=np.float32,
        order="C",
        copy=True,
    )

    logger.debug(f"FAISS embeddings shape: "f"{embeddings.shape}")
    logger.debug(f"FAISS embeddings dtype: "f"{embeddings.dtype}")
    logger.debug(f"C-contiguous: "f"{embeddings.flags['C_CONTIGUOUS']}")


    d = embeddings.shape[1]

    index = faiss.IndexFlatIP(d)

    index.add(embeddings)

    if save:
        faiss.write_index(index,str(PROCESSED_DATA_DIR /f"all_features_limit_{limit}_index.index"))

    return index


if __name__ == "__main__":

    LIMIT = 31034

    metadata_path = (PROCESSED_DATA_DIR /"metadata_index_reprocessed.csv")
    metadata_df = pd.read_csv(metadata_path)


    if "faiss_id" not in metadata_df.columns:

        metadata_df["faiss_id"] = metadata_df.index
        metadata_df.to_csv(metadata_path,index=False,)

    if LIMIT < 31034:
        feature_path = (PROCESSED_DATA_DIR /f"similarity_features_{LIMIT}.parquet" )
    else:
        feature_path = (PROCESSED_DATA_DIR /"full_extraction_parts"/"similarity_features_part_0_4000.parquet")

    if not feature_path.exists():
        logger.info("Feature parquet does not exist. ""Extracting features...")
        extract_features(metadata_df,limit=LIMIT,save=True)

    features_df = pd.read_parquet(feature_path)

    logger.info(f"Loaded {len(features_df)} songs")


    embeddings_df = produce_embeddings(features_df,limit=LIMIT,weights=None,save=True,save_unweighted=True)

    index = produce_FAISS_index(embeddings_df.to_numpy(dtype=np.float32,copy=True,),limit=LIMIT,save=True)


    logger.debug(f"Embedding shape: "f"{embeddings_df.shape}")
    logger.debug( f"FAISS index size: " f"{index.ntotal}")
    logger.info(embeddings_df.head())

