from pathlib import Path
import h5py
from tqdm import tqdm
import pandas as pd

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

if __name__ == "__main__":
    files = list(Path("data/midi_metadata").rglob("*.h5"))
    metadata = [extract_h5_metadata(f) for f in tqdm(files)]
    print(f"Extracted metadata for {len(metadata)} files.")
    df = pd.DataFrame(metadata)
    df.to_csv("data/metadata_index.csv", index=False)