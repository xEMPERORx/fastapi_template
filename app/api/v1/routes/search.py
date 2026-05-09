from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependency_factory import get_search_service
from app.core.logger import log_function
from app.schema.search import SearchResponse
from app.services.search.service import SearchService


router = APIRouter(tags=["Search"])

@router.get("/", response_model=SearchResponse)
@log_function
async def general_search(
    search_service: Annotated[SearchService, Depends(get_search_service)],
    q: str = Query(..., min_length=2),
    resource_type: str = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    return await search_service.search(
        query_text=q,
        resource_type=resource_type,
        page=page,
        limit=limit,
    )
