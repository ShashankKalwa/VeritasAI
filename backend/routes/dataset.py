"""
GET /api/dataset — Browsable dataset endpoint
"""
import logging
from fastapi import APIRouter, Query
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/dataset")
async def get_dataset(
    label: str = Query(default="all"),
    category: str = Query(default="All"),
    search: str = Query(default=""),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, le=100),
):
    """Return paginated dataset with filters."""
    try:
        sb = get_supabase()
        query = sb.table("dataset").select("*", count="exact")

        if label and label != "all":
            query = query.eq("label", label)
        if category and category != "All":
            query = query.eq("category", category)
        if search:
            query = query.ilike("headline", f"%{search}%")

        from_idx = (page - 1) * page_size
        to_idx = from_idx + page_size - 1

        resp = query.order("id").range(from_idx, to_idx).execute()

        total = resp.count or 0
        total_pages = (total + page_size - 1) // page_size

        return {
            "data": resp.data or [],
            "count": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
        }

    except Exception as e:
        logger.error(f"Dataset error: {e}")
        return {"data": [], "count": 0, "page": 1, "pageSize": page_size, "totalPages": 0}


@router.get("/api/dataset/stats")
async def get_dataset_stats():
    """Return dataset summary statistics."""
    try:
        sb = get_supabase()
        resp = sb.table("dataset").select("label, category").execute()
        data = resp.data or []

        total = len(data)
        fake_count = sum(1 for d in data if d["label"] == "fake")
        real_count = sum(1 for d in data if d["label"] == "real")
        categories = list(set(d["category"] for d in data))

        return {
            "total": total,
            "fakeCount": fake_count,
            "realCount": real_count,
            "categories": categories,
        }
    except Exception as e:
        logger.error(f"Dataset stats error: {e}")
        return {"total": 0, "fakeCount": 0, "realCount": 0, "categories": []}
