from pydantic import BaseModel


class Song(BaseModel):
    id: int
    title: str
    artist_name: str


class SearchResult(Song):
    score: float


class GraphNode(Song):
    type: str


class GraphEdge(BaseModel):
    source: int
    target: int
    weight: float


class Graph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]