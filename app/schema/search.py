from pydantic import BaseModel


class SearchResult(BaseModel):
    id: str
    type: str
    name: str
    score: float


class SearchResponse(BaseModel):
    total: int
    results: list[SearchResult]
