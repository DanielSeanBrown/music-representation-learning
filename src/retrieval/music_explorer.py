from pathlib import Path

import faiss
import numpy as np
import pandas as pd

import sys
from src.config.paths import PROCESSED_DATA_DIR



class MusicExplorer:
    """
    Music retrieval and exploration backend.

    Assumptions:
    - metadata has columns: faiss_id, track, artist_name_name_name_name_name_name_name_name_name_name_name
    - embeddings are already StandardScaled + L2 normalised
    - FAISS index was built from embeddings in the same row order
    """

    def __init__(
        self,
        metadata: pd.DataFrame,
        embeddings: np.ndarray,
        index: faiss.Index
    ):
        self.metadata = metadata
        self.embeddings = embeddings
        self.index = index

    @classmethod
    def load(
        cls,
        metadata_path: str | Path,
        embeddings_path: str | Path,
        index_path: str | Path,
    ):
        """
        Load metadata, embeddings and FAISS index from disk.
        """

        metadata_path = Path(metadata_path)
        embeddings_path = Path(embeddings_path)
        index_path = Path(index_path)

        if metadata_path.suffix == ".parquet":
            metadata = pd.read_parquet(metadata_path)
        elif metadata_path.suffix == ".csv":
            metadata = pd.read_csv(metadata_path)
        else:
            raise ValueError(
                "Metadata must be .parquet or .csv"
            )

        embeddings = np.load(embeddings_path)

        index = faiss.read_index(str(index_path))

        return cls(
            metadata=metadata,
            embeddings=embeddings,
            index=index
        )

    def get_song(
        self,
        faiss_id: int
    ) -> dict:
        """
        Return metadata for a song.
        """

        row = self.metadata.loc[
            self.metadata["faiss_id"] == faiss_id
        ]

        if len(row) == 0:
            raise ValueError(
                f"Song ID {faiss_id} not found."
            )

        return row.iloc[0].to_dict()

    def find_song(
        self,
        title_name: str
    ) -> pd.DataFrame:
        """
        Find songs whose title contains title_name.
        """

        matches = self.metadata[
            self.metadata["title"]
            .str.contains(
                title_name,
                case=False,
                na=False
            )
        ]

        return matches

    def get_neighbours(
        self,
        faiss_id: int,
        k: int = 10
    ) -> list[dict]:
        """
        Retrieve k nearest neighbours from FAISS.
        """

        query = self.embeddings[
            faiss_id:faiss_id + 1
        ]

        D, I = self.index.search(
            query,
            k + 1
        )

        results = []

        for idx, score in zip(
            I[0][1:],      # skip self
            D[0][1:]
        ):

            row = self.metadata.iloc[idx]

            results.append(
                {
                    "id": int(idx),
                    "title": row["title"],
                    "artist_name": row["artist_name"],
                    "score": float(score)
                }
            )

        return results

    def search(
        self,
        title_name: str,
        k: int = 10
    ) -> list[dict]:
        """
        Search by title name and return neighbours.
        """

        matches = self.find_song(title_name)

        if len(matches) == 0:
            raise ValueError(
                f"No title found matching '{title_name}'"
            )

        faiss_id = int(
            matches.iloc[0]["faiss_id"]
        )

        return self.get_neighbours(
            faiss_id=faiss_id,
            k=k
        )

    def get_graph(
        self,
        faiss_id: int,
        k: int = 5
    ) -> dict:
        """
        Return a simple graph structure suitable
        for Cytoscape.js / React frontend.
        """

        nodes = []
        edges = []

        center_song = self.get_song(faiss_id)

        nodes.append(
            {
                "id": faiss_id,
                "title": center_song["title"],
                "artist_name": center_song["artist_name"],
                "type": "query"
            }
        )

        neighbours = self.get_neighbours(
            faiss_id=faiss_id,
            k=k
        )

        for neighbour in neighbours:

            nodes.append(
                {
                    "id": neighbour["id"],
                    "title": neighbour["title"],
                    "artist_name": neighbour["artist_name"],
                    "type": "neighbour"
                }
            )

            edges.append(
                {
                    "source": faiss_id,
                    "target": neighbour["id"],
                    "weight": neighbour["score"]
                }
            )

        return {
            "nodes": nodes,
            "edges": edges
        }

    def get_two_hop_graph(
        self,
        faiss_id: int,
        k: int = 5
    ) -> dict:
        """
        Expand neighbourhood to 2 hops.
        Useful for future graph visualisation.
        """

        nodes = {}
        edges = []

        center_song = self.get_song(faiss_id)

        nodes[faiss_id] = {
            "id": faiss_id,
            "title": center_song["title"],
            "artist_name": center_song["artist_name"],
            "type": "query"
        }

        first_hop = self.get_neighbours(
            faiss_id=faiss_id,
            k=k
        )

        for neighbour in first_hop:

            nid = neighbour["id"]

            nodes[nid] = {
                "id": nid,
                "title": neighbour["title"],
                "artist_name": neighbour["artist_name"],
                "type": "hop_1"
            }

            edges.append(
                {
                    "source": faiss_id,
                    "target": nid,
                    "weight": neighbour["score"]
                }
            )

            second_hop = self.get_neighbours(
                faiss_id=nid,
                k=k
            )

            for second in second_hop:

                sid = second["id"]

                if sid not in nodes:

                    nodes[sid] = {
                        "id": sid,
                        "title": second["title"],
                        "artist_name": second["artist_name"],
                        "type": "hop_2"
                    }

                edges.append(
                    {
                        "source": nid,
                        "target": sid,
                        "weight": second["score"]
                    }
                )

        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }



if __name__ == '__main__':

    metadata = pd.read_csv("metadata_index.csv")
    embeddings = np.load(f"{PROCESSED_DATA_DIR}/all_features_limit_20_embeddings.npy")
    index = faiss.read_index(f"{PROCESSED_DATA_DIR}/all_features_limit_20_index.index")

    # explorer = MusicExplorer(
    #     metadata,
    #     embeddings,
    #     index
    # )

    # Search by title
    # results = explorer.search(
    #     "Man in the Mirror",
    #     k=10
    # )
    # print(results)

    # Graph for frontend
    # graph = explorer.get_graph(
    #     song_id=123,
    #     k=5
    # )
    # print(graph)

    # Two-hop graph
    # graph_2 = explorer.get_two_hop_graph(
    #     song_id=123,
    #     k=5
    # )
    # print(graph_2)