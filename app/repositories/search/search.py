from elasticsearch import AsyncElasticsearch

from app.core.circuit_breakers import es_breaker
from app.core.logger import LoggedRepository
from app.core.recovery import RetryConfig, async_retry


class SearchRepository(LoggedRepository):
    def __init__(self, es_client: AsyncElasticsearch):
        self.es_client = es_client
        self.index_name = "search_index"

    async def search(
        self,
        query_text: str,
        resource_type: str | None,
        page: int,
        limit: int,
    ) -> dict:
        offset = (page - 1) * limit

        search_query = {
            "bool": {
                "should": [
                    {
                        "multi_match": {
                            "query": query_text,
                            "type": "bool_prefix",
                            "fields": [
                                "name^5",
                                "name._2gram^3",
                                "name._3gram^3",
                                "city^3",
                                "genre^2",
                            ],
                            "fuzziness": "AUTO",
                        }
                    },
                    {
                        "wildcard": {
                            "name": {
                                "value": f"*{query_text.lower()}*",
                                "boost": 1.0,
                            }
                        }
                    },
                ]
            }
        }

        filters: list[dict] = []
        if resource_type:
            filters.append({"term": {"type": resource_type}})

        query = {
            "from": offset,
            "size": limit,
            "query": {
                "bool": {
                    "must": [search_query],
                    "filter": filters,
                }
            },
            "highlight": {
                "fields": {
                    "name": {},
                    "city": {},
                    "genre": {},
                }
            },
            "sort": [{"_score": {"order": "desc"}}],
        }

        async def _do_search():
            return await self.es_client.search(index=self.index_name, body=query)

        return await es_breaker.call(
            async_retry, _do_search, config=RetryConfig(max_retries=2, base_delay=0.2)
        )
