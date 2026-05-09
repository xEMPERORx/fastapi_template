from app.repositories.search.search import SearchRepository
from app.schema.search import SearchResponse, SearchResult
from app.core.logger import LoggedService


class SearchService(LoggedService):
    def __init__(self, repo: SearchRepository):
        self.repo = repo

    async def search(
        self,
        query_text: str,
        resource_type: str | None,
        page: int,
        limit: int,
    ) -> SearchResponse:
        response = await self.repo.search(
            query_text=query_text,
            resource_type=resource_type,
            page=page,
            limit=limit,
        )

        hits = response.get("hits", {})
        hit_items = hits.get("hits", [])
        total_value = hits.get("total", {}).get("value", 0)

        results: list[SearchResult] = []
        for hit in hit_items:
            source = hit.get("_source", {})
            if not source:
                continue

            results.append(
                SearchResult(
                    id=str(source.get("id", "")),
                    type=str(source.get("type", "")),
                    name=str(source.get("name", "")),
                    score=float(hit.get("_score") or 0.0),
                )
            )

        return SearchResponse(total=total_value, results=results)
