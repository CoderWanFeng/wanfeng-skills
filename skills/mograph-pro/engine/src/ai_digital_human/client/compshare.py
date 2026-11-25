"""优云智算 Compshare 上的 ComfyUI API 客户端。"""

from __future__ import annotations

import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Optional

import requests


class CompshareError(RuntimeError):
    """ComfyUI 请求、执行或输出解析失败。"""


class CompshareClient:
    """访问独立部署的 ComfyUI，不携带 MiniMax 鉴权。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        request_timeout: int = 180,
        retries: int = 2,
    ) -> None:
        self.base_url = (base_url or os.getenv("COMPSHARE_BASE_URL", "")).strip().rstrip("/")
        if not self.base_url:
            raise RuntimeError("自托管 H3 需要设置 COMPSHARE_BASE_URL 或传 --compshare-base-url")
        self.request_timeout = request_timeout
        self.retries = retries
        self.client_id = uuid.uuid4().hex
        self.session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        last_error: Optional[requests.RequestException] = None
        for attempt in range(self.retries + 1):
            try:
                resp = self.session.request(
                    method,
                    f"{self.base_url}{path}",
                    timeout=self.request_timeout,
                    **kwargs,
                )
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"server error {resp.status_code}: {resp.text[:300]}")
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(1.5 * (attempt + 1))
        raise CompshareError(f"ComfyUI 请求失败：{method} {path}：{last_error}")

    def _upload(self, path: str | Path, *, kind: str) -> str:
        path = Path(path).expanduser().resolve()
        if not path.is_file():
            raise RuntimeError(f"上传素材不存在：{path}")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        with path.open("rb") as handle:
            resp = self._request(
                "POST",
                f"/api/upload/{kind}",
                data={"name": path.name, "type": "input", "subfolder": ""},
                files={kind: (path.name, handle, mime)},
            )
        payload = resp.json()
        item = payload[0] if isinstance(payload, list) and payload else payload
        name = item.get("name") or item.get("filename") if isinstance(item, dict) else None
        if not name:
            raise CompshareError(f"上传 {path.name} 后未返回文件名：{payload}")
        return name

    def upload_image(self, path: str | Path) -> str:
        return self._upload(path, kind="image")

    def upload_audio(self, path: str | Path) -> str:
        return self._upload(path, kind="audio")

    def submit(self, workflow: dict) -> str:
        resp = self._request(
            "POST",
            "/api/prompt",
            json={"prompt": workflow, "client_id": self.client_id},
        )
        payload = resp.json()
        prompt_id = payload.get("prompt_id") or payload.get("promptId")
        if not prompt_id:
            raise CompshareError(f"任务提交后未返回 prompt_id：{payload}")
        return str(prompt_id)

    def history(self, prompt_id: str) -> dict:
        return self._request("GET", f"/api/history/{prompt_id}").json()

    @staticmethod
    def video_output(history_entry: dict) -> dict:
        """只从正式 output 区找视频，忽略 preview 等临时结果。"""
        outputs = history_entry.get("outputs") or {}
        candidates: list[dict] = []

        def collect(value) -> None:
            if isinstance(value, list):
                for child in value:
                    collect(child)
            elif isinstance(value, dict):
                if value.get("filename"):
                    candidates.append(value)
                else:
                    for child in value.values():
                        collect(child)

        collect(outputs)
        for item in candidates:
            if item.get("type") != "output":
                continue
            filename = item.get("filename") or ""
            if Path(filename).suffix.lower() in (".mp4", ".mov", ".webm", ".mkv"):
                return item
        raise CompshareError(f"历史结果的 type=output 中没有视频：{outputs}")

    def wait(self, prompt_id: str, *, timeout: int = 3600, poll_interval: float = 5.0) -> dict:
        started = time.monotonic()
        while time.monotonic() - started < timeout:
            payload = self.history(prompt_id)
            entry = payload.get(prompt_id) if isinstance(payload, dict) else None
            if entry:
                status = entry.get("status") or {}
                if status.get("status_str") == "error":
                    raise CompshareError(f"ComfyUI 执行失败：{status.get('messages') or status}")
                self.video_output(entry)
                return entry
            time.sleep(poll_interval)
        raise TimeoutError(f"ComfyUI 任务 {prompt_id} 超过 {timeout} 秒仍未产出视频")

    def download(self, output: dict, out_path: str | Path) -> Path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        resp = self._request(
            "GET",
            "/view",
            params={
                "filename": output["filename"],
                "subfolder": output.get("subfolder", ""),
                "type": "output",
            },
        )
        out_path.write_bytes(resp.content)
        return out_path
