from elasticsearch import AsyncElasticsearch
from app.settings import Config

ES_HOST = Config.ELASTICSEARCH_URL

es_client = AsyncElasticsearch(
    hosts=[ES_HOST],
    retry_on_timeout=True,
    max_retries=10
)

async def get_es_client():
    try:
        yield es_client
    finally:
        pass

async def close_es_client():
    await es_client.close()


INDEX_NAME = "search_index"
INDEX_CONFIG = {
    "settings": {
        "analysis": {
            "analyzer": {
                "autocomplete": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "edge_ngram_filter"],
                }
            },
            "filter": {
                "edge_ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                }
            },
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "type": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "autocomplete",
                "search_analyzer": "standard",
                "fields": {"raw": {"type": "keyword"}},
            },
            "city": {"type": "text"},
            "genre": {"type": "text"},
        }
    },
}
