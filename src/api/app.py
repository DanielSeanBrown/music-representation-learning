from fastapi import FastAPI

from src.retrieval.load import load_data
from src.retrieval.music_explorer import MusicExplorer

metadata, embeddings, index = load_data()

explorer = MusicExplorer(
    metadata,
    embeddings,
    index
)

app = FastAPI()

@app.get("/search")
def search(
    query: str,
    k: int = 10
):
    return explorer.search(
        query,
        k
    )