from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.retrieval.load import load_data
from src.retrieval.music_explorer import MusicExplorer


# ==============================================================
# Load data
# ==============================================================

metadata, embeddings, index, unweighted_features = load_data()

explorer = MusicExplorer(
    metadata=metadata,
    embeddings=embeddings,
    index=index,
    unweighted_features=unweighted_features,
)


# ==============================================================
# FastAPI
# ==============================================================

app = FastAPI(
    title="Music Explorer API",
    description="API for music similarity search and exploration.",
)


# ==============================================================
# CORS
# ==============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==============================================================
# SEARCH
# ==============================================================

# ==============================================================
# SEARCH
# ==============================================================

@app.get("/search")
def search(
    query: str | None = None,
    artist: str | None = None,
    limit: int = None,
):
    """
    Search for songs by title or artist.

    Exactly one of query or artist should normally be supplied.
    """

    if not query and not artist:
        return []

    if query:
        return explorer.find_songs(
            query=query,
            limit=limit,
        )

    return explorer.find_songs_by_artist(
        query=artist,
        limit=limit,
    )

# ==============================================================
# GET SONG
# ==============================================================

@app.get("/songs/{faiss_id}")
def get_song(
    faiss_id: int,
):
    """
    Return metadata for a single song.
    """

    try:

        return explorer.get_song(
            faiss_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ==============================================================
# GET NEIGHBOURS
# ==============================================================

@app.get("/songs/{faiss_id}/neighbours")
def get_neighbours(
    faiss_id: int,
    k: int = 10,
):
    """
    Return the k most similar songs using
    whichever similarity mode is currently active.
    """

    try:

        return explorer.get_neighbours(
            faiss_id=faiss_id,
            k=k,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ==============================================================
# ONE-HOP GRAPH
# ==============================================================

@app.get("/songs/{faiss_id}/graph")
def get_graph(
    faiss_id: int,
    k: int = 5,
):
    """
    Return a one-hop similarity graph.
    """

    try:

        return explorer.get_graph(
            faiss_id=faiss_id,
            k=k,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ==============================================================
# TWO-HOP GRAPH
# ==============================================================

@app.get("/songs/{faiss_id}/graph/two-hop")
def get_two_hop_graph(
    faiss_id: int,
    k: int = 5,
):
    """
    Return a two-hop similarity graph.
    """

    try:

        return explorer.get_two_hop_graph(
            faiss_id=faiss_id,
            k=k,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ==============================================================
# SHORTEST PATH
# ==============================================================

@app.get("/songs/{start_id}/path/{end_id}")
def shortest_path(
    start_id: int,
    end_id: int,
    k: int = 10,
):
    """
    Find the shortest path using the currently
    active similarity index.
    """

    try:

        return explorer.get_shortest_path(
            start_id=start_id,
            end_id=end_id,
            k=k,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ==============================================================
# SIMILARITY / WEIGHT STATUS
# ==============================================================

@app.get("/similarity/status")
def similarity_status():
    """
    Return the currently active similarity mode
    and custom weighting information.
    """

    return explorer.get_similarity_status()


# ==============================================================
# BUILD CUSTOM WEIGHTS
# ==============================================================

@app.post("/similarity/custom")
def build_custom_similarity(
    weights: dict,
):
    """
    Build a new in-memory FAISS index using
    custom feature-group weights.

    The original/default FAISS index is never modified.
    """

    try:

        explorer.build_custom_index(
            weights
        )

        return {
            "success": True,
            **explorer.get_similarity_status(),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


# ==============================================================
# USE DEFAULT SIMILARITY
# ==============================================================

@app.post("/similarity/default")
def use_default_similarity():
    """
    Switch back to the original FAISS index.
    """

    explorer.use_default_index()

    return {
        "success": True,
        **explorer.get_similarity_status(),
    }


# ==============================================================
# USE CUSTOM SIMILARITY
# ==============================================================

@app.post("/similarity/custom/activate")
def use_custom_similarity():
    """
    Activate the previously-created custom FAISS index.
    """

    try:

        explorer.use_custom_index()

        return {
            "success": True,
            **explorer.get_similarity_status(),
        }

    except RuntimeError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )