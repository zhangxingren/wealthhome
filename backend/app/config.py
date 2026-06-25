"""应用配置"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 服务端口
    port: int = 8000

    # JWT 密钥 — 必须通过环境变量注入，拒绝默认值
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 168  # 7 天

    # 数据库路径（容器内 /app/data/wealthhome.db；本地开发用当前目录）
    db_path: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wealthhome.db"))

    # Tushare token（免费用户，仅支持日线行情）
    tushare_token: str = os.getenv("TUSHARE_TOKEN", "")

    # 行情自动刷新间隔（分钟），0 表示不自动刷新
    market_refresh_interval: int = int(os.getenv("MARKET_REFRESH_INTERVAL", "0"))


settings = Settings()

if not settings.jwt_secret:
    raise ValueError("JWT_SECRET 环境变量未设置，拒绝启动")
