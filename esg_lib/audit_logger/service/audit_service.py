from esg_lib.audit_logger.models.AuditLog import AuditLog
from esg_lib.decorators import catch_exceptions
from esg_lib.paginator import Paginator
from esg_lib.filters import build_filters


@catch_exceptions
def get_audit_logs_paginated(args, data):
    query = build_filters(data.get("filters", []))

    if "action" not in query:
        query["action"] = {"$ne": "RETRIEVE"}

    page = args.get("page")
    per_page = args.get("size")
    sort_by = args.get("sort_key", "id")
    sort_order = args.get("sort_order", -1)

    collection = AuditLog().db()
    skip = max((page - 1) * per_page, 0)
    total_items = collection.aggregate(
        [
            {"$match": query},
            {"$sort": {sort_by: sort_order}},
            {"$skip": skip},
            {"$limit": per_page},
        ]
    )

    data = [AuditLog(**entity) for entity in total_items]
    total = collection.find(query, {"_id": 1}).count()

    return Paginator(data, page, per_page, total)
