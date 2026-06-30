"""统一API响应格式"""

from typing import Any, Optional

def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}

def error(code: int = 1, message: str = "error", detail: Any = None) -> dict:
    return {"code": code, "message": message, "detail": detail}

def paginated(items: list, total: int, page: int = 1, page_size: int = 20) -> dict:
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    }
