"""用户设置同步 API — 隐藏资产等偏好跨设备同步

分层架构：Router → Repository → Database
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from app.core.auth import get_current_user
from app.repositories.asset_repo import raw_query, raw_query_one, raw_execute

router = APIRouter(prefix="/api/user", tags=["settings"])


class SettingUpdate(BaseModel):
    value: Any


@router.get("/settings")
def get_settings(current_user: dict = Depends(get_current_user)):
    user_id = int(current_user["sub"])
    rows = raw_query(
        "SELECT setting_key, setting_value FROM user_settings WHERE user_id = ?",
        (user_id,),
    )
    result = {}
    for row in rows:
        try:
            result[row["setting_key"]] = json.loads(row["setting_value"])
        except (json.JSONDecodeError, TypeError):
            result[row["setting_key"]] = row["setting_value"]
    return result


@router.put("/settings/{setting_key}")
def put_setting(
    setting_key: str,
    body: SettingUpdate,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    value_str = json.dumps(body.value, ensure_ascii=False)

    existing = raw_query_one(
        "SELECT id FROM user_settings WHERE user_id = ? AND setting_key = ?",
        (user_id, setting_key),
    )
    if existing:
        raw_execute(
            "UPDATE user_settings SET setting_value = ? WHERE user_id = ? AND setting_key = ?",
            (value_str, user_id, setting_key),
        )
    else:
        raw_execute(
            "INSERT INTO user_settings (user_id, setting_key, setting_value) VALUES (?, ?, ?)",
            (user_id, setting_key, value_str),
        )

    return {"ok": True, "key": setting_key}
