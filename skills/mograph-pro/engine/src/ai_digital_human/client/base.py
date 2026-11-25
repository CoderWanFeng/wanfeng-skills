"""MiniMax 开放平台公共配置、鉴权与错误处理。

同一套接口有两种接入方式，用 `DH_MINIMAX_ROUTE` 切换：

- `official`    —— 官方开放平台，密钥 `MINIMAX_API_KEY`，地址默认 `https://api.minimax.cn`
- `recommended` —— 我们推荐的平台（聚合/中转），密钥 `MINIMAX_RECOMMENDED_API_KEY`，
                   地址必须由 `MINIMAX_RECOMMENDED_BASE_URL` 指定

两条路由走的是同一套 HTTP 接口，只是地址和密钥不同，所以上层代码不需要分支。
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

import requests

# 两条接入路由的配置项。地址为空表示必须由用户显式填写。
ROUTES: dict[str, dict[str, str]] = {
    "official": {
        "label": "官方 API",
        "key_env": "MINIMAX_API_KEY",
        "base_env": "MINIMAX_OFFICIAL_BASE_URL",
        "default_base": "https://api.minimax.cn",
    },
    "recommended": {
        "label": "推荐平台 API",
        "key_env": "MINIMAX_RECOMMENDED_API_KEY",
        "base_env": "MINIMAX_RECOMMENDED_BASE_URL",
        "default_base": "",
    },
}

# 兼容旧引用：未显式切路由时的官方地址
API_BASE = os.getenv("MINIMAX_API_BASE", "https://api.minimax.cn").rstrip("/")
TIMEOUT = 180


class MiniMaxError(RuntimeError):
    """平台返回非 0 状态码时抛出。"""

    def __init__(self, code: int, message: str, trace_id: str = "") -> None:
        super().__init__(f"[{code}] {message}" + (f" (trace_id={trace_id})" if trace_id else ""))
        self.code = code
        self.message = message
        self.trace_id = trace_id


def load_env_file() -> None:
    """从项目根目录的 .env 读取环境变量。

    .env 优先于外部环境变量，避免 shell 中残留的旧 Key 覆盖项目配置。
    """
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name:
            os.environ[name] = value


def minimax_route() -> str:
    """当前 MiniMax 接入路由：official（官方）或 recommended（推荐平台）。"""
    route = (os.getenv("DH_MINIMAX_ROUTE", "official") or "official").strip().lower()
    if route not in ROUTES:
        raise RuntimeError(
            f"未知的 MiniMax 路由 {route!r}，只能是 {' / '.join(ROUTES)}"
        )
    return route


def route_config() -> dict[str, str]:
    return ROUTES[minimax_route()]


def route_label() -> str:
    return route_config()["label"]


def api_base() -> str:
    """按当前路由返回接口根地址。"""
    cfg = route_config()
    value = os.getenv(cfg["base_env"], "").strip() or cfg["default_base"]
    if not value:
        raise RuntimeError(
            f"{cfg['label']} 需要设置 {cfg['base_env']}，"
            "例如 https://你的平台域名（不要带结尾斜杠）"
        )
    return value.rstrip("/")


def api_key() -> str:
    load_env_file()
    cfg = route_config()
    key = os.getenv(cfg["key_env"], "").strip()
    if not key:
        raise RuntimeError(
            f"环境变量 {cfg['key_env']} 未设置（当前路由：{cfg['label']}）。"
            "要么填这个变量，要么把 DH_MINIMAX_ROUTE 改回 official"
        )
    return key


def headers(extra: Optional[dict] = None) -> dict:
    base = {"Authorization": f"Bearer {api_key()}"}
    base.update(extra or {})
    return base


def params() -> dict:
    """老式鉴权需要额外携带 GroupId。"""
    group_id = os.getenv("MINIMAX_GROUP_ID", "").strip()
    return {"GroupId": group_id} if group_id else {}


def raise_for_status(payload: dict) -> dict:
    base = payload.get("base_resp") or {}
    code = base.get("status_code", 0)
    if code != 0:
        raise MiniMaxError(code, base.get("status_msg", "unknown error"), payload.get("trace_id", ""))
    return payload


def request_json(
    method: str,
    url: str,
    *,
    json_body: Optional[dict] = None,
    retries: int = 2,
    timeout: int = TIMEOUT,
) -> dict:
    """发起 JSON 请求，失败时按退避重试。"""
    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            resp = requests.request(
                method,
                url,
                headers=headers({"Content-Type": "application/json"}),
                params=params(),
                json=json_body,
                timeout=timeout,
            )
            if resp.status_code >= 500:
                raise requests.HTTPError(f"server error {resp.status_code}: {resp.text[:200]}")
            resp.raise_for_status()
            return raise_for_status(resp.json())
        except (requests.RequestException, MiniMaxError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise last_error  # type: ignore[misc]
