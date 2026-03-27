def parse_pagination(args, default_page_size=20, max_page_size=100):
    try:
        page = max(int(args.get("page", 1) or 1), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = max(
            int(args.get("page_size", default_page_size) or default_page_size), 1
        )
    except (TypeError, ValueError):
        page_size = default_page_size

    page_size = min(page_size, max_page_size)
    skip = (page - 1) * page_size
    return {"page": page, "page_size": page_size, "skip": skip}


def build_pagination_meta(page, page_size, total):
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
