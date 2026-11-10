"""MiniMax 开放平台公共配置、鉴权与错误处理。"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

import requests

API_BASE = os.getenv("MINIMAX_API_BASE", "https://api.minimax.cn").rstrip("/")
TIMEOUT = 180


class MiniMaxError(RuntimeError):
    """平台返回非 0 状态码时抛出。"""

    def __init__(self, code: int, message: str, trace_id: str = "") -> None:
        super().__init__(f"[{code}] {message}" + (f" (trace_id={trace_id})" if trace_id else ""))
        self.code = code
        self.message = message
        self.trace_id = trace_id


def find_work_root() -> Path:
    """定位工作目录根：优先 DH_WORK_ROOT，其次向上找含 .env 或 scripts/build.py 的目录。

    Skill 会把引擎复制到用户工作目录后再运行，目录层级不固定，
    因此不能再用写死的 parents[3]。
    """
    override = os.getenv("DH_WORK_ROOT", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    current = Path(__file__).resolve().parent
    for candidate in (current, *current.parents):
        if (candidate / ".env").is_file() or (candidate / "scripts" / "build.py").is_file():
            return candidate
    return Path(__file__).resolve().parents[3]


def load_env_file() -> None:
    """从工作目录根目录的 .env 读取环境变量。

    .env 优先于外部环境变量，避免 shell 中残留的旧 Key 覆盖项目配置。
    """
    env_path = find_work_root() / ".env"
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


def api_key() -> str:
    load_env_file()
    key = os.getenv("MINIMAX_API_KEY", "").strip()
    if not key:
        raise RuntimeError("环境变量 MINIMAX_API_KEY 未设置")
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
