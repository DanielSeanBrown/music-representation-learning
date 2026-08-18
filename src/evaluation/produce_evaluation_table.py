import pandas as pd
from pathlib import Path

from src.config.paths import PROCESSED_DATA_DIR


def produce_evaluation_table(limit: int = None, save: bool = False, skip: int = None) -> pd.DataFrame:
    """Produce an evaluation table for human evaluation of track similarity.
    
    For every three tracks in the metadata_index.csv file, the first track is considered the root track,
    and the next two tracks are candidates for comparison. The user is prompted to choose which of the two candidate tracks is more similar to the root track
    The results are stored in an evaluation table. To skip a comparison, the user can simply press Enter without making a choice.

    The evaluation table will contain the following columns:
        root_track          - The root track for comparison
        closer_track        - The track that is more similar to the root track
        further_track       - The track that is less similar to the root track
        root_track_id       - The ID of the root track
        closer_track_id     - The ID of the closer track
        further_track_id    - The ID of the further track
        
    Args:
        limit (int, optional): The maximum number of tracks to include in the evaluation table. Defaults to None.
        save (bool, optional): Whether to save the evaluation table as a parquet file. Defaults to False.
        skip (int, optional): The number of tracks to skip from the beginning of the metadata_index.csv file. Defaults to None.

    Returns:
        pd.DataFrame: The evaluation table.
    """

    metadata = pd.read_csv(PROCESSED_DATA_DIR / "metadata_index.csv")
    evaluation_table = dict(root_track=[], closer_track=[], further_track=[], root_track_id=[], closer_track_id=[], further_track_id=[])

    if skip is not None:
        metadata = metadata.iloc[skip:]

    if limit is not None:
        metadata = metadata.head(limit)
    
    for index, row in metadata.iterrows():
       if index % 3 == 0:
            if index + 2 >= len(metadata):
                break
            root_track = metadata.iloc[index]
            candidate_track_a = metadata.iloc[index + 1]
            candidate_track_b = metadata.iloc[index + 2]
            print("comparison", index // 3 + 1, "of", len(metadata) // 3)
            choice = input(f"Root Track: \n{root_track['artist_name']} - {root_track['title']}\n\nCandidate Track A: \n{candidate_track_a['artist_name']} - {candidate_track_a['title']}\n\nCandidate Track B: \n{candidate_track_b['artist_name']} - {candidate_track_b['title']}\n\nWhich track is more similar to the root track? (A/B or C if comparison tracks are closer to each other): ")
            if choice.lower() == "a":
                evaluation_table["root_track"].append(f"{root_track['artist_name']} - {root_track['title']}")
                evaluation_table["closer_track"].append(f"{candidate_track_a['artist_name']} - {candidate_track_a['title']}")
                evaluation_table["further_track"].append(f"{candidate_track_b['artist_name']} - {candidate_track_b['title']}")
                evaluation_table["root_track_id"].append(root_track["track_id"])
                evaluation_table["closer_track_id"].append(candidate_track_a["track_id"])
                evaluation_table["further_track_id"].append(candidate_track_b["track_id"])
            elif choice.lower() == "b":
                evaluation_table["root_track"].append(f"{root_track['artist_name']} - {root_track['title']}")
                evaluation_table["closer_track"].append(f"{candidate_track_b['artist_name']} - {candidate_track_b['title']}")
                evaluation_table["further_track"].append(f"{candidate_track_a['artist_name']} - {candidate_track_a['title']}")
                evaluation_table["root_track_id"].append(root_track["track_id"])
                evaluation_table["closer_track_id"].append(candidate_track_b["track_id"])
                evaluation_table["further_track_id"].append(candidate_track_a["track_id"])
            elif choice.lower() == "c":
                evaluation_table["root_track"].append(f"{candidate_track_a['artist_name']} - {root_track['title']}")
                evaluation_table["closer_track"].append(f"{candidate_track_b['artist_name']} - {candidate_track_a['title']}")
                evaluation_table["further_track"].append(f"{root_track['artist_name']} - {candidate_track_b['title']}")
                evaluation_table["root_track_id"].append(candidate_track_a["track_id"])
                evaluation_table["closer_track_id"].append(candidate_track_b["track_id"])
                evaluation_table["further_track_id"].append(root_track["track_id"])
            elif choice == "":
                print("Skipping this comparison.")

    evaluation_df = pd.DataFrame(evaluation_table)

    if save:
        if Path(PROCESSED_DATA_DIR / "evaluation_table.parquet").exists() is True:
            overwrite = str(input("evaluation_table.parquet already exists. Do you want to overwrite or append to it? (O/A): "))
            if overwrite.lower != "a":
                evaluation_df.to_parquet(PROCESSED_DATA_DIR / "evaluation_table.parquet", index=False)
            elif overwrite.lower == "a":
                existing_df = pd.read_parquet(PROCESSED_DATA_DIR / "evaluation_table.parquet")
                combined_df = pd.concat([existing_df, evaluation_df], ignore_index=True)
                combined_df.drop_duplicates(subset=["root_track_id", "closer_track_id", "further_track_id"], inplace=True)
                combined_df.to_parquet(PROCESSED_DATA_DIR / "evaluation_table.parquet", index=False)

        evaluation_df.to_parquet(PROCESSED_DATA_DIR / "evaluation_table.parquet", index=False)

    return evaluation_df


if __name__ == "__main__":
    print(produce_evaluation_table(limit=360, save=True).head())