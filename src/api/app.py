from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.retrieval.load import load_data
from src.retrieval.music_explorer import MusicExplorer



"""This script is for initialising the FastAPI app for the music explorer.
It loads the necessary data (metadata, embeddings, FAISS index, and unweighted feature groups)
and sets up the API endpoints for:
- Searching for songs by title or artist
- Retrieving metadata for a single song
- Getting the k most similar songs
- Building a one-hop similarity graph
- Building a two-hop similarity graph
- Finding the shortest path between two songs
- Managing similarity modes (default, custom, and custom activation)
"""

metadata, embeddings, index, unweighted_features = load_data()

explorer = MusicExplorer(
    metadata=metadata,
    embeddings=embeddings,
    index=index,
    unweighted_features=unweighted_features,
)




app = FastAPI(
    title="Music Explorer API",
    description="API for music similarity search and exploration.",
)



"""
React runs on localhost:5173.
FastAPI runs on localhost:8000.
CORSMiddleware allows communication between the two ports.
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/search")
def search(
    query: str | None = None,
    artist: str | None = None,
    limit: int = None,
):
    """
    This function calls to search for songs by title or artist.
    Args:
        query (str | None): The title of the song to search for.
        artist (str | None): The name of the artist to search for.
        limit (int | None): The maximum number of results to return. Defaults to None.

    Returns:
        list: A list of songs matching the search criteria.
    """

    if not query and not artist:
        return []

    if query:
        return explorer.find_songs(query=query, limit=limit)

    return explorer.find_songs_by_artist(query=artist, limit=limit)


@app.get("/songs/{faiss_id}")
def get_song(
    faiss_id: int,
):
    """
    This function calls to retrieve metadata for a single song based on its FAISS ID.

    Args:
        faiss_id (int): The FAISS ID of the song to retrieve.

    Returns:
        dict: Metadata of the requested song.
    """

    try:
        return explorer.get_song(faiss_id)
    
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))




@app.get("/songs/{faiss_id}/neighbours")
def get_neighbours(
    faiss_id: int,
    k: int = 10,
):
    """
    This function calls to retrieve the k most similar songs to the given FAISS ID.

    Args:
        faiss_id (int): The FAISS ID of the reference song.
        k (int): The number of similar songs to retrieve. Defaults to 10.

    Returns:
        list: A list of the k most similar songs based on the current similarity mode.
    """

    try:
        return explorer.get_neighbours(faiss_id=faiss_id, k=k)

    except ValueError as error:
        raise HTTPException( status_code=404, detail=str(error))


@app.get("/songs/{faiss_id}/graph")
def get_graph(
    faiss_id: int,
    k: int = 5,
):
    """
    This function calls to retrieve a one-hop similarity graph for the given FAISS ID.

    Args:
        faiss_id (int): The FAISS ID of the reference song.
        k (int): The number of similar songs to include in the graph. Defaults to 5.

    Returns:
        dict: A one-hop similarity graph for the given FAISS ID.
    """

    try:
        return explorer.get_graph(faiss_id=faiss_id,  k=k)

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.get("/songs/{faiss_id}/graph/two-hop")
def get_two_hop_graph(
    faiss_id: int,
    k: int = 5,
):
    """
    This function calls to retrieve a two-hop similarity graph for the given FAISS ID.

    Args:
        faiss_id (int): The FAISS ID of the reference song.
        k (int): The number of similar songs to include in the graph. Defaults to 5.

    Returns:
        dict: A two-hop similarity graph for the given FAISS ID.
    """

    try:
        return explorer.get_two_hop_graph(faiss_id=faiss_id, k=k)

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))



@app.get("/songs/{start_id}/path/{end_id}")
def shortest_path(
    start_id: int,
    end_id: int,
    k: int = 10,
):
    """
    This function calls to find the shortest path between two songs using the currently
    active similarity index.

    Args:
        start_id (int): The FAISS ID of the starting song.
        end_id (int): The FAISS ID of the target song.
        k (int): The number of similar songs to consider at each step. Defaults to 10.

    Returns:
        list: A list of FAISS IDs representing the shortest path from the start song to the end song.
    """

    try:

        return explorer.get_shortest_path(start_id=start_id, end_id=end_id, k=k)

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.get("/similarity/status")
def similarity_status():
    """
    This function calls to retrieve the current similarity status.
    
    Returns:
        dict: The currently active similarity mode and custom weighting information.
    """

    return explorer.get_similarity_status()


@app.post("/similarity/custom")
def build_custom_similarity(
    weights: dict,
):
    """
    This function calls to build and create a new in-memory FAISS index using
    the provided custom feature-group weights. The original/default FAISS index is not modified.

    Args:
        weights (dict): A dictionary containing the custom feature-group weights.

    Returns:
        dict: The updated similarity status after building the custom index.
    """

    try:
        explorer.build_custom_index(weights)

        return {
            "success": True,
            **explorer.get_similarity_status(),
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/similarity/default")
def use_default_similarity():
    """
    This function calls to switch back to the original FAISS index.
    """

    explorer.use_default_index()

    return {
        "success": True,
        **explorer.get_similarity_status(),
    }


@app.post("/similarity/custom/activate")
def use_custom_similarity():
    """
    This function calls to activate the previously-created custom FAISS index.
    """

    try:
        explorer.use_custom_index()

        return {
            "success": True,
            **explorer.get_similarity_status(),
        }

    except RuntimeError as error:
        raise HTTPException(status_code=400, detail=str(error))