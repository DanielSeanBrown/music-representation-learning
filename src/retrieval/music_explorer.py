from pathlib import Path
import heapq

import faiss
import numpy as np
import pandas as pd


class MusicExplorer:
    """This class is for completing the actions needed for the music retrieval and exploration backend.
    It lets you do the following:
        - Use the Default FAISS similarity index or build a custom one with weighted feature groups
        - Song lookup by FAISS ID
        - Song lookup by title
        - Song lookup by artist
        - Similarity search using the active FAISS index
        - Get a one-hop graph
        - Get a two-hop graph
        - Perform Dijkstra shortest path search"""


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

    DEFAULT_WEIGHTS = {
        "stats": 1.0,
        "chroma": 1.0,
        "entropy": 0.5,
        "rhythm": 1.0,
        "structure": 0.5,
        "melody": 0.5,
        "low": 0.5,
        "mid": 0.5,
        "high": 0.5,
    }

    def __init__(
        self,
        metadata: pd.DataFrame,
        embeddings: np.ndarray,
        index: faiss.Index,
        unweighted_features: dict | None = None,
    ):

        self.metadata = metadata
        self.embeddings = embeddings

        self.default_index = index

        self.custom_index = None
        self.custom_embeddings = None
        self.custom_weights = self.DEFAULT_WEIGHTS.copy()
        self.unweighted_features = unweighted_features

        self.index = index # this is the active index, it is the provided default index at initialization, but can be switched to a custom one.
        self.mode = "default"


    @classmethod
    def load(
        cls,
        metadata_path: str | Path,
        embeddings_path: str | Path,
        index_path: str | Path,
        unweighted_features_path: str | Path | None = None,
    ):
        """Loads the metadata, embeddings, and FAISS index from disk. Optionally loads unweighted feature groups for custom weighting.
        Args:
            metadata_path (str | Path): Path to the metadata CSV.
            embeddings_path (str | Path): Path to the embeddings .npy file.
            index_path (str | Path): Path to the FAISS index file.
            unweighted_features_path (str | Path | None): Path to the optional unweighted feature groups .npz file.
        Returns:
            MusicExplorer: An instance of the MusicExplorer class with loaded data."""

        metadata_path = Path(metadata_path)
        embeddings_path = Path(embeddings_path)
        index_path = Path(index_path)


        metadata = pd.read_csv(metadata_path)
        embeddings = np.load(embeddings_path).astype(np.float32,copy=False,)
        index = faiss.read_index(str(index_path))


        unweighted_features = None
        if unweighted_features_path is not None:

            unweighted_features_path = Path(unweighted_features_path)

            if unweighted_features_path.exists():

                loaded = np.load(unweighted_features_path)

                unweighted_features = {}
                for name in cls.FEATURE_GROUPS:
                    if name in loaded.files:
                        unweighted_features[name] = (loaded[name].astype(np.float32,copy=False))

        return cls(
            metadata=metadata,
            embeddings=embeddings,
            index=index,
            unweighted_features=unweighted_features,
        )

 

    def _get_metadata_row(
        self,
        faiss_id: int,
    ) -> pd.Series:
        """
        Given a FAISS ID, return the corresponding row from the metadata DataFrame.
        Often FAISS IDs are equal to the row index, but this is not guaranteed.
        As such, we always resolve the metadata using the "faiss_id" column.

        The function also checks that the ID exists and is unique in the metadata. If not, it raises a ValueError.
        By the construction of the metadata, this should never happen, but in testing there were some issues with prior FAISS ID assignments, so this is a safeguard.
        """

        faiss_id = int(faiss_id)

        matches = self.metadata[self.metadata["faiss_id"] == faiss_id]

        if matches.empty:
            raise ValueError(f"Song ID {faiss_id} not found.")
        if len(matches) > 1:
            raise ValueError(f"Song ID {faiss_id} appears multiple times in metadata.")

        return matches.iloc[0]


    def _song_from_id(
        self,
        faiss_id: int,
    ) -> dict:
        """This is a helper function to get the song information from the metadata given a FAISS ID. 
        Args:
            faiss_id (int): The FAISS ID of the song.
        Returns:
            dict: A dictionary containing the song's ID, title, and artist name.
        """

        row = self._get_metadata_row(faiss_id)

        return {
            "id": int(faiss_id),
            "title": str(row["title"]),
            "artist_name": str(row["artist_name"])
        }


    def build_custom_index(
        self,
        weights: dict,
    ):
        """ This function builds a custom FAISS index using the user provided weights for each feature group.
        As with when the embeddings were weighted originally, the weights should be a dictionary where 
        keys are feature group names and values are the corresponding weights.

        The function validates the weights, constructs a weighted embedding matrix, normalizes it, and creates a new FAISS index.

        Args:
            weights (dict): A dictionary containing the weights for each feature group.
            Keys should be feature group names, and values should be the corresponding weights.
        """

        # Check that the user hasn't made all weights zero
        validated_weights = {}
        for name in self.FEATURE_GROUPS:
            validated_weights[name] = weights.get(name,self.DEFAULT_WEIGHTS[name])

        if all(value == 0 for value in validated_weights.values()):
            raise ValueError("At least one feature-group weight must be greater than zero.")

        weighted_groups = []

        for name in self.FEATURE_GROUPS:

            embeddings = self.unweighted_features[name]
            weight = validated_weights[name]

            weighted = (embeddings * weight).astype(np.float32,copy=False)
            weighted_groups.append(weighted)

        custom_embeddings = np.concatenate(weighted_groups,axis=1)

        # Previous issues with FAISS and non-contiguous arrays leads us to ensure the array is contiguous and of type float32
        custom_embeddings = np.array(custom_embeddings,dtype=np.float32,order="C",copy=True)

        faiss.normalize_L2(custom_embeddings)

        custom_index = faiss.IndexFlatIP(custom_embeddings.shape[1])
        custom_index.add(custom_embeddings)

        self.custom_embeddings = custom_embeddings
        self.custom_index = custom_index
        self.custom_weights = validated_weights

        # switch over from default
        self.index = self.custom_index 
        self.mode = "custom"


    def use_default_index(self):
        """ This function switches the active FAISS index back to the default one, discarding any custom index that may have been built. """

        self.index = self.default_index
        self.mode = "default"

    def use_custom_index(self):
        """ This function switches the active FAISS index to the custom one, if it has been built.
        If no custom index exists, it raises a RuntimeError. """

        if self.custom_index is None:
            raise RuntimeError("No custom index has been built.")

        self.index = self.custom_index
        self.mode = "custom"



    def get_similarity_status(self):
        """ This function returns the current similarity mode (default or custom) and the weights being used for the active index.

        Returns:
            dict:
                the current similarity mode : str
                the active weights : dict
                whether a custom index is available : bool
        """

        return {
            "mode": self.mode,
            "weights": (self.custom_weights.copy() if self.mode == "custom" else self.DEFAULT_WEIGHTS.copy()),
            "custom_available": self.custom_index is not None,
        }


    def get_song(
        self,
        faiss_id: int,
    ) -> dict:
        """Given a FAISS ID, return the corresponding song information from the metadata.
        Args:
            faiss_id (int): The FAISS ID of the song.
        Returns:
            dict: A dictionary containing the song's ID, title, and artist name."""

        row = self._get_metadata_row(faiss_id)
        song = row.astype(object).where(pd.notna(row),None)
        result = song.to_dict()
        result["id"] = int(faiss_id) # This is added explicitly to ensure the ID is always present, even if the metadata row is missing it.

        return result



    def find_songs(
        self,
        query: str,
        limit: int = None,
    ) -> list[dict]:
        
        """This function searches for songs by title.
        It performs a case-insensitive search and returns a list of matching songs,
        each represented as a dictionary containing the song's ID, title, and artist name."""

        matches = self.metadata[
            self.metadata["title"].str.contains(
                query,
                case=False,
                na=False,
                regex=False,
            )
        ]

        # Restrict results if a limit is provided
        if limit is not None:
            if limit > 0:
                matches = matches.head(limit)

        results = []

        for _, row in matches.iterrows():
            results.append(
                {
                    "id": row["faiss_id"],
                    "title": row["title"],
                    "artist_name": row["artist_name"]
                }
            )

        return results


    def find_songs_by_artist(
        self,
        query: str,
        limit: int = None,
    ) -> list[dict]:
        
        """This function searches for songs by artist name.
        It performs a case-insensitive search and returns a list of matching songs,
        each represented as a dictionary containing the song's ID, title, and artist name."""

        matches = self.metadata[
            self.metadata["artist_name"].str.contains(
                query,
                case=False,
                na=False,
                regex=False,
            )
        ]

        # Restrict results if a limit is provided
        if limit is not None:
            if limit > 0:
                matches = matches.head(limit)

        results = []

        for _, row in matches.iterrows():
            results.append(
                {
                    "id": row["faiss_id"],
                    "title": row["title"],
                    "artist_name": row["artist_name"]
                }
            )

        return results

    def get_neighbours(
        self,
        faiss_id: int,
        k: int = 10,
    ) -> list[dict]:
        """Given a FAISS ID, return the k most similar songs based on the active FAISS index.
        Args:
            faiss_id (int): The FAISS ID of the query song.
            k (int, optional): The number of similar songs to retrieve. Defaults to 10.
        Returns:
            list[dict]: A list of dictionaries, each containing the ID, title, and artist name of a similar song.
        """



        self._get_metadata_row(faiss_id)


        # Validate FAISS ID
        if (faiss_id < 0 or faiss_id >= self.index.ntotal):
            raise ValueError(f"Invalid FAISS ID: {faiss_id}")

        # Validate k
        if k < 1:
            raise ValueError("k must be at least 1.")

        # Validate custom index availability if in custom mode
        if self.mode == "custom":
            if self.custom_embeddings is None:
                raise RuntimeError("Custom embeddings are not available.")
            query = self.custom_embeddings[faiss_id:faiss_id + 1].copy()

        else:
            query = self.embeddings[faiss_id:faiss_id + 1].copy()
            faiss.normalize_L2(query)


        # Search and recieve distances and indices of the k nearest neighbours
        distances, indices = self.index.search(query, k + 1)

        results = []

        for idx, score in zip(indices[0], distances[0]):
            
            idx = int(idx)

            # skip qurery song
            if idx == faiss_id:
                continue

            row = self._get_metadata_row(idx)

            results.append(
                {
                    "id": idx,
                    "title": str(row["title"]),
                    "artist_name": str(row["artist_name"]),
                    "score": float(score)
                }
            )

        return results


    def get_graph(
        self,
        faiss_id: int,
        k: int = 5,
    ) -> dict[str, list[dict]]:
        
        """Given a FAISS ID, return a graph representation of the song and its k nearest neighbours.
        Args:
            faiss_id (int): The FAISS ID of the query song.
            k (int, optional): The number of similar songs to retrieve. Defaults to 5.
        Returns:
            dict: A dictionary containing nodes and edges representing the graph.
        """

        nodes = []
        edges = []

        # Root track
        center_song = self.get_song(faiss_id)
        nodes.append(
            {
                "id": faiss_id,
                "title": center_song["title"],
                "artist_name": center_song["artist_name"],
                "type": "query"
            }
        )


        neighbours = self.get_neighbours(faiss_id=faiss_id, k=k)

        for neighbour in neighbours:
            nid = int(neighbour["id"])

            nodes.append(
                {
                    "id":nid,
                    "title": neighbour["title"],
                    "artist_name": neighbour["artist_name"],
                    "type": "hop_1"
                }
            )

            edges.append(
                {
                    "source": faiss_id,
                    "target": nid,
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
        k: int = 5,
    ) -> dict[str, list[dict]]:
        """This an extension of the get_graph function,
        where this retrieves a two-hop graph instead of a one-hop graph.
        
        Args:
            faiss_id (int): The FAISS ID of the query song.
            k (int, optional): The number of similar songs to retrieve for each hop. Defaults to 5.
        Returns:
            dict: A dictionary containing nodes and edges representing the two-hop graph.
        """

        nodes = {}
        edges = {}

        center_song = self.get_song(faiss_id)

        nodes[faiss_id] = {
            "id": faiss_id,
            "title": center_song["title"],
            "artist_name": center_song["artist_name"],
            "type": "query",
        }


        # get immediate neighbours
        first_hop = self.get_neighbours(faiss_id=faiss_id, k=k)

        for neighbour in first_hop:

            nid = int(neighbour["id"])

            nodes[nid] = {
                "id": nid,
                "title": neighbour["title"],
                "artist_name": neighbour["artist_name"],
                "type": "hop_1",
            }

            edge_key = tuple(sorted((faiss_id,nid)))
            edges[edge_key] = float(neighbour["score"])


        # get neighbours of neighbours
        for neighbour in first_hop:

            nid = neighbour["id"]

            second_hop = self.get_neighbours(faiss_id=nid, k=k)

            for second in second_hop:

                sid = second["id"]

                # skip root song
                if sid == faiss_id:
                    continue



                if sid not in nodes:

                    nodes[sid] = {
                        "id": sid,
                        "title": second["title"],
                        "artist_name": second["artist_name"],
                        "type": "hop_2"
                    }

                edge_key = tuple(sorted((nid, sid)))
                score = float(second["score"])

                # Deal with case where bidirectional edges exists with differing scores
                if (edge_key not in edges or score > edges[edge_key]):
                    edges[edge_key] = score


        edge_list = [
            {
                "source": int(source),
                "target": int(target),
                "weight": float(weight),
            }

            for (source, target), weight in edges.items()
        ]

        return {
            "nodes": list(nodes.values()),
            "edges": edge_list
        }


    def get_shortest_path(
        self,
        start_id: int,
        end_id: int,
        k: int = 10,
    ) -> dict:
        """This function implements Dijkstra's algorithm to find the shortest path between two songs in the similarity graph.
        Args:
            start_id (int): The FAISS ID of the starting song.
            end_id (int): The FAISS ID of the ending song.
            k (int, optional): The number of similar songs to consider for each hop. Defaults to 10.
        Returns:
            dict: A dictionary containing the nodes, edges, and total cost of the shortest path.
        """

        # validate that both start and end IDs exist in the metadata
        self._get_metadata_row(start_id)
        self._get_metadata_row(end_id)

        # If the start and end IDs are the same, return a trivial path
        if start_id == end_id:
            song = self.get_song(start_id)

            return {
                "nodes": 
                [
                    {
                        "id": start_id,
                        "title": song["title"],
                        "artist_name": song["artist_name"],
                        "type": "start",
                        "position": 0
                    }
                ],
                "edges": [],
                "total_cost": 0.0
            }


        distances = {start_id: 0.0}
        previous = {}
        queue = [(0.0, start_id)]
        visited = set()

        while queue:
            current_cost, current_id = heapq.heappop(queue)
            
            if current_id in visited:
                continue

            visited.add(current_id)

            if current_id == end_id:
                break

            neighbours = self.get_neighbours(faiss_id=current_id, k=k)

            for neighbour in neighbours:

                neighbour_id = neighbour["id"]
                similarity = neighbour["score"]
            
                edge_cost = max(0.0, 1.0 - similarity) # Ensure non-negative cost
                new_cost = (current_cost +edge_cost)

                # Update the distance and previous node if this path is better
                if neighbour_id not in distances or new_cost < distances[neighbour_id]:

                    distances[neighbour_id] = new_cost
                    previous[neighbour_id] = {
                        "node": current_id,
                        "similarity": similarity,
                    }

                    heapq.heappush(
                        queue,
                        (
                            new_cost,
                            neighbour_id,
                        ),
                    )

        # No path found if the end_id is not in distances
        if end_id not in distances:

            return {
                "nodes": [],
                "edges": [],
                "total_cost":None,
            }

        # Reconstruct the path from end_id to start_id using the previous dictionary
        path = []
        current_id = end_id
        while True:
            path.append(current_id)
            if current_id == start_id:
                break
            current_id = previous[current_id]["node"]
        path.reverse()

        # Reconstruct the nodes for the path
        nodes = []
        for position, song_id in enumerate(path):

            song = self.get_song(song_id)
            if song_id == start_id:
                node_type = "start"
            elif song_id == end_id:
                node_type = "end"
            else:
                node_type = "path"
            nodes.append(
                {
                    "id": song_id,
                    "title": song["title"],
                    "artist_name": song["artist_name"],
                    "type": node_type,
                    "position": position
                }
            )

        # Reconstruct the edges for the path
        edges = []
        for position in range(len(path) - 1):

            source = path[position]
            target = path[position + 1]

            similarity = previous[target]["similarity"]
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "similarity": similarity,
                    "cost": 1.0 - similarity,
                }
            )

        return {
            "nodes": nodes,
            "edges": edges,
            "total_cost": float(distances[end_id])
        }