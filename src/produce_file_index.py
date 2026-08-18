from pathlib import Path
from src.config.paths import MSD_METADATA_DIR, PROCESSED_DATA_DIR
import h5py
from tqdm import tqdm
import pandas as pd
from loguru import logger

def extract_h5_metadata(h5_path) -> dict:
    "Given the path to an h5 file, extract the relevant metadata and return it as a dictionary."
    with h5py.File(h5_path, "r") as h5:

        song = h5["metadata"]["songs"][0]
        midi_path = str(h5_path).replace("midi_metadata", "midi_files").replace(".h5", "")

        return {
            "track_id": Path(h5_path).stem,
            "artist_name": song["artist_name"].decode("utf-8"),
            "artist_id": song["artist_id"].decode("utf-8"),
            "title": song["title"].decode("utf-8"),
            "song_id": song["song_id"].decode("utf-8"),
            "release": song["release"].decode("utf-8"),
            "genre": song["genre"].decode("utf-8"),
            "midi_path": midi_path
        }

def extract_metadata():
    """Produces and saves a metadata file for traversing and understanding the 
    .midi and .h5 files as downloaded from the Lakh MIDI Dataset"""

    files = list(Path(MSD_METADATA_DIR).rglob("*.h5"))

    metadata = [extract_h5_metadata(f) for f in tqdm(files)]

    logger.info(f"Extracted metadata for {len(metadata)} files.")

    df = pd.DataFrame(metadata)
    df.to_csv(f"{PROCESSED_DATA_DIR}/metadata_index.csv", index=False)

if __name__ == "__main__":
    extract_metadata()