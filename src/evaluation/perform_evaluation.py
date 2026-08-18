from pathlib import Path

from itertools import product

import faiss
import numpy as np
import pandas as pd
from tqdm import tqdm

from loguru import logger

from src.config.paths import PROCESSED_DATA_DIR, UNWEIGHTED_PATH


FEATURE_NAMES = [
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

WEIGHT_RANGES = { 
    "stats": (0.0, 5.0),
    "chroma": (0.0, 5.0),
    "entropy": (0.0, 5.0),
    "rhythm": (0.0, 5.0),
    "structure": (0.0, 5.0),
    "melody": (0.0, 5.0),
    "low": (0.0, 5.0),
    "mid": (0.0, 5.0),
    "high": (0.0, 5.0),
}



def load_unweighted_embeddings(load_path: Path = UNWEIGHTED_PATH) -> dict:
    """
    Load the standardised feature groups before weighting. Each feature group is stored as a numpy array.

    Args:
        load_path (Path): Path to the .npz file containing the unweighted embeddings.
    Returns:
        feature_groups : dict - Dictionary containing one numpy array per feature group.
    """

    if not load_path.exists():
        logger.error(f"Could not find unweighted embeddings file: {load_path}")

    data = np.load(load_path)

    feature_groups = {}

    for name in FEATURE_NAMES:

        if name not in data:
            logger.error(f"Feature group '{name}' is missing from {load_path}")

        feature_groups[name] = np.asarray(data[name], dtype=np.float32, order="C")

    n_songs = next(iter(feature_groups.values())).shape[0] # Get the number of songs from any feature group

    logger.info(f"Loaded {n_songs} songs.")
    logger.info("Feature dimensions:")
    for name, array in feature_groups.items():
        logger.info(f"  {name:12s}: {array.shape[1]:5d}")

    
    logger.info(f"\nTotal dimensions: {sum(array.shape[1]for array in feature_groups.values())}")

    return feature_groups



def load_track_id_mapping(n_embeddings: int, metadata_path: Path = PROCESSED_DATA_DIR / "metadata_index_reprocessed.csv") -> dict:
    """
    Loads metadata and creates a mapping from track_id to embedding row index.
    This mapping is essential for evaluating triplets,
    as it allows us to convert track IDs into the corresponding row indices in the embeddings array.

    The row order in metadata_index_reprocessed.csv must match the row order used when creating the unweighted embeddings.

    Args:
        n_embeddings (int): The number of embeddings in the unweighted embeddings file.
        metadata_path (Path): Path to the metadata_index_reprocessed.csv file containing track IDs and other metadata.
    Returns:
        track_id_to_index : dict - A dictionary mapping track_id to its corresponding row index in the embeddings array.
    """

    # Check if the metadata file exists
    if not metadata_path.exists():
        logger.error(f"Could not find metadata file: {metadata_path}")

    metadata = pd.read_csv(metadata_path)

    # Crop metadata to match the number of embeddings if necessary
    if len(metadata) != n_embeddings:
        metadata = metadata.head(n_embeddings)


    track_id_to_index = {track_id: index for index, track_id in enumerate(metadata["track_id"])}

    logger.info(f"Created mapping for {len(track_id_to_index)} track IDs.")

    return track_id_to_index



def load_triplets(
    track_id_to_index: dict,
    triplets_path: Path = PROCESSED_DATA_DIR / "evaluation_table.parquet"
) -> pd.DataFrame:
    """
    Load evaluation triplets and convert track IDs into embedding indices.

    Triplets containing tracks that are no longer present in the metadata
    are removed.
    """

    if not triplets_path.exists():
        logger.error(f"Could not find triplets file: {triplets_path}")

    triplets = pd.read_parquet(triplets_path)

    logger.info(f"Loaded {len(triplets)} triplets.")

    valid = pd.Series(True, index=triplets.index)

    for column in [
        "root_track_id",
        "closer_track_id",
        "further_track_id"
    ]:

        mapped = triplets[column].map(track_id_to_index)

        missing = mapped.isna()

        if missing.any():
            logger.warning(
                f"{missing.sum()} triplets have a missing "
                f"'{column}' track ID."
            )

        triplets[
            column.replace("_track_id", "_embedding_index")
        ] = mapped

        valid &= mapped.notna()

    removed = (~valid).sum()

    if removed:
        logger.warning(
            f"Removing {removed} triplets containing tracks "
            f"that are not present in the embeddings."
        )

    triplets = triplets.loc[valid].copy()

    # Now that all NaNs have been removed, conversion is safe.
    for column in [
        "root_embedding_index",
        "closer_embedding_index",
        "further_embedding_index"
    ]:
        triplets[column] = triplets[column].astype(np.int64)

    logger.info(
        f"Using {len(triplets)} valid triplets for evaluation."
    )

    return triplets



def sample_weights(rng: np.random.Generator, feature_names: list = FEATURE_NAMES) -> dict:
    """
    Generate one random weighting configuration.
    All weights are sampled independently from uniform distributions defined in WEIGHT_RANGES.

    Args:
        rng (np.random.Generator): A random number generator instance for reproducibility.
    Returns:
        dict: A dictionary containing one weight per feature group where weights are sampled independently from uniform distributions.
    """

    weights = {}

    for name in feature_names:

        minimum, maximum = WEIGHT_RANGES[name]
        weights[name] = rng.uniform(minimum, maximum)

    return weights



def build_weighted_embedding(feature_groups: dict, weights: dict, features: list = FEATURE_NAMES) -> np.ndarray:
    """
    Apply feature-group weights and concatenate them.

    Args:
        feature_groups (dict): Dictionary containing one numpy array per feature group.
        weights (dict): Dictionary containing one weight per feature group.
    Returns:
        np.ndarray: The weighted and concatenated embedding.
    """

    parts = []

    for name in features:
        part = feature_groups[name]* weights[name]
        parts.append(part)

    embedding = np.concatenate(parts,axis=1,)

    return np.asarray(embedding,dtype=np.float32,order="C")



def normalise_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """ This function L2-normalises embeddings.
    After this, taking dot product will be equivalent to cosine similarity.

    Args:
        embeddings (np.ndarray): The embeddings to normalise.
    REturns:
        np.ndarray: The L2-normalised embeddings.
    """

    embeddings = np.asarray(embeddings,dtype=np.float32,order="C",).copy()
    faiss.normalize_L2(embeddings)

    return embeddings


def produce_discrete_weightings(feature_names: list = FEATURE_NAMES, weight_ranges: dict = WEIGHT_RANGES) -> list:
    """
    Produce a list of discrete weightings for each feature group.
    These are made up of complete combinations of maximum, minimum and medium weightings.

    Args:
        feature_names (list): List of feature group names.
        weight_ranges (dict): Dictionary specifying the min and max weight for each feature group.
    Returns:
        list: A list of dictionaries, each containing one discrete weighting configuration.
    """

    discrete_weightings =  []
    feature_weights = {name: [] for name in feature_names}
    for name in feature_names:
        minimum, maximum = weight_ranges[name]
        medium = (minimum + maximum) / 2
        feature_weights[name] = [minimum, medium, maximum]

    # Generate all combinations of discrete weightings
    keys = feature_names
    values = [feature_weights[name] for name in keys]
    for combination in product(*values):
        discrete_weightings.append(dict(zip(keys, combination)))

    return discrete_weightings


def evaluate_triplets(embeddings: np.ndarray, triplets: pd.DataFrame) -> tuple:
    """
    Takes a set of embeddings and a DataFrame of triplets, and evaluates the triplet accuracy.
    For each triplet, it checks if the cosine similarity between the root 
    and closer embeddings is greater than the cosine similarity between the root and further embeddings.

    Because the embeddings are L2-normalised, the dot product is equivalent to cosine similarity.

    Args:
        embeddings (np.ndarray): The embeddings to evaluate.
        triplets (pd.DataFrame): DataFrame containing the evaluation triplets with embedding indices.

    Returns:
        tuple: A tuple containing:
            accuracy (float): The proportion of triplets for which the closer embedding is more similar to the root than the further embedding.
            mean_margin (float): The mean difference in similarity between the closer and further embeddings.
            median_margin (float): The median difference in similarity between the closer and further embeddings.
            std_margin (float): The standard deviation of the difference in similarity between the closer and further embeddings.
    """

    # Use the embedding indices from the triplets DataFrame to retrieve the corresponding embeddings
    roots = embeddings[triplets["root_embedding_index"].to_numpy(dtype=np.int64)]
    closer = embeddings[triplets["closer_embedding_index"].to_numpy(dtype=np.int64)]
    further = embeddings[triplets["further_embedding_index"].to_numpy(dtype=np.int64)]

    closer_similarity = np.sum(roots * closer,axis=1)
    further_similarity = np.sum(roots * further,axis=1)

    margins = (closer_similarity - further_similarity)
    correct = margins > 0

    accuracy = correct.mean()
    mean_margin = margins.mean()
    median_margin = np.median(margins)
    std_margin = np.std(margins)

    return (
        accuracy,
        mean_margin,
        median_margin,
        std_margin,
    )



def evaluate(limit: int, n_trials: int, random_seed: int, save: bool) -> pd.DataFrame:
    """Perform a randomised as well as specific search over feature-group weightings and evaluate them using the triplet evaluation set.
    Args:
        limit (int): The maximum number of tracks to include in the evaluation table.
        n_trials (int): The number of random weightings to evaluate.
        random_seed (int): The random seed for reproducibility.
        save (bool): Whether to save the evaluation results as a parquet file.

    Returns:
        pd.DataFrame: DataFrame containing the evaluation results for each trial.
    """

    rng = np.random.default_rng(random_seed)

    feature_groups = load_unweighted_embeddings()

    n_embeddings = next(iter(feature_groups.values())).shape[0] # Get the number of embeddings from any feature group

    track_id_to_index = load_track_id_mapping(n_embeddings)
    triplets = load_triplets(track_id_to_index)


    results = []
    # randomised search over weightings
    for trial in tqdm(range(n_trials),desc="Evaluating randomised weightings"):

        weights = sample_weights(rng)
        embeddings = build_weighted_embedding(feature_groups,weights)
        embeddings = normalise_embeddings(embeddings)
        
        accuracy, mean_margin, median_margin, std_margin = evaluate_triplets(embeddings,triplets)


        result = {
            "trial": trial,
            "accuracy": accuracy,
            "mean_margin": mean_margin,
            "median_margin": median_margin,
            "std_margin": std_margin,
        }

        for name in FEATURE_NAMES:
            result[f"weight_{name}"] = weights[name]

        results.append(result)

    # predefined weightings
    discrete_weightings = produce_discrete_weightings(FEATURE_NAMES, WEIGHT_RANGES)
    for trial in tqdm(range(n_trials, n_trials + len(discrete_weightings)), desc="Evaluating predefined weightings"):

        weights = discrete_weightings[trial - n_trials]
        embeddings = build_weighted_embedding(feature_groups,weights)
        embeddings = normalise_embeddings(embeddings)
        
        accuracy, mean_margin, median_margin, std_margin = evaluate_triplets(embeddings,triplets)


        result = {
            "trial": trial,
            "accuracy": accuracy,
            "mean_margin": mean_margin,
            "median_margin": median_margin,
            "std_margin": std_margin,
        }

        for name in FEATURE_NAMES:
            result[f"weight_{name}"] = weights[name]

        results.append(result)



    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("accuracy",ascending=False).reset_index(drop=True)
    

    logger.info(f"Best trial: {results_df.iloc[0]['trial']} with accuracy: {results_df.iloc[0]['accuracy']:.3f}")

    best_weighting = results_df.loc[0, [col for col in results_df.columns if col.startswith("weight_")]].to_dict()
    logger.info(f"Best weighting: {best_weighting}")

    if save:
        results_df.to_parquet(PROCESSED_DATA_DIR / f"weight_evaluation_limit_{limit}.parquet",index=False,)
        best_weighting_df = pd.DataFrame([best_weighting])
        best_weighting_df.to_parquet(PROCESSED_DATA_DIR / f"best_weighting_limit_{limit}.parquet",index=False,)

    return results_df



if __name__ == "__main__":

    LIMIT = 31034
    N_TRIALS = 20000
    RANDOM_SEED = 19

    evaluate(limit=LIMIT, n_trials=N_TRIALS, random_seed=RANDOM_SEED, save=True)