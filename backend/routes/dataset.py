"""
GET /api/dataset — Browsable dataset endpoint (v2 label mapping)
"""
import logging
from fastapi import APIRouter, Query, Request
from lib.supabase_client import get_supabase
from lib.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# Display label mapping: DB values → v2 taxonomy
LABEL_MAP = {
    "fake": "False",
    "real": "Credible",
    "FAKE": "False",
    "REAL": "Credible",
}


def _map_label(label: str) -> str:
    """Map old REAL/FAKE labels to v2 taxonomy for display."""
    return LABEL_MAP.get(label, label)


@router.get("/api/dataset")
@limiter.limit("30/minute")
async def get_dataset(
    request: Request,
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

        # Map v2 filter labels back to DB values for querying
        if label and label != "all":
            # Accept both old and new label names
            db_label = label
            if label == "False":
                db_label = "fake"
            elif label == "Credible":
                db_label = "real"
            query = query.eq("label", db_label)
        if category and category != "All":
            query = query.eq("category", category)
        if search:
            query = query.ilike("headline", f"%{search}%")

        from_idx = (page - 1) * page_size
        to_idx = from_idx + page_size - 1

        resp = query.order("id").range(from_idx, to_idx).execute()

        # Map labels for display
        data = resp.data or []
        for row in data:
            row["display_label"] = _map_label(row.get("label", ""))

        total = resp.count or 0
        total_pages = (total + page_size - 1) // page_size

        return {
            "data": data,
            "count": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": total_pages,
        }

    except Exception as e:
        logger.error(f"Dataset error: {e}")
        return {"data": [], "count": 0, "page": 1, "pageSize": page_size, "totalPages": 0}


@router.get("/api/dataset/stats")
@limiter.limit("30/minute")
async def get_dataset_stats(request: Request):
    """Return dataset summary statistics."""
    try:
        sb = get_supabase()
        resp = sb.table("dataset").select("label, category").limit(1000).execute()
        data = resp.data or []

        total = len(data)
        false_count = sum(1 for d in data if d["label"] in ("fake", "FAKE"))
        credible_count = sum(1 for d in data if d["label"] in ("real", "REAL"))
        categories = list(set(d["category"] for d in data))

        return {
            "total": total,
            "falseCount": false_count,
            "credibleCount": credible_count,
            "categories": categories,
        }
    except Exception as e:
        logger.error(f"Dataset stats error: {e}")
        return {"total": 0, "falseCount": 0, "credibleCount": 0, "categories": []}
