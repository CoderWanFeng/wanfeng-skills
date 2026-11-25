#!/usr/bin/env python3
"""体检：验证环境变量里的 API Key 是否可用于语音接口。

会发起一次极短的真实合成（2 个字符，约 0.0004 元），用于确认鉴权与模型可用。

用法：
    python3 scripts/check_env.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ai_digital_human import MiniMaxError, t2a  # noqa: E402
from ai_digital_human.client import load_env_file  # noqa: E402


def main() -> int:
    load_env_file()
    key = os.getenv("MINIMAX_API_KEY", "").strip()
    print(f"MINIMAX_API_KEY：{'已设置（长度 %d，前缀 %s…）' % (len(key), key[:9]) if key else '未设置'}")
    group_id = os.getenv("MINIMAX_GROUP_ID", "").strip()
    print(f"MINIMAX_GROUP_ID：{group_id if group_id else '未设置（新版接口通常不需要）'}")
    if not key:
        print("请先 export MINIMAX_API_KEY=...")
        return 1

    try:
        result = t2a("测试", model="speech-2.8-turbo", voice_id="female-tianmei", retries=0)
    except MiniMaxError as exc:
        print(f"鉴权失败：{exc}")
        if exc.code in (2049, 1004):
            print("→ 该 Key 无效或不属于开放平台。订阅/中转通道的 Key 不能调用开放平台语音接口，"
                  "请到 platform.minimax.cn 账户管理 → 接口密钥 重新创建。")
        elif exc.code == 1008:
            print("→ 账户余额不足，请先充值。")
        elif exc.code == 2038:
            print("→ 账号未完成实名认证，音色复刻需要个人或企业认证。")
        return 1
    except Exception as exc:  # 网络等其他异常
        print(f"请求异常：{type(exc).__name__} {exc}")
        return 1

    print(f"鉴权正常 ✓  合成成功：时长 {result.duration_ms / 1000:.2f}s，"
          f"计费字符 {result.charged_chars}，trace_id {result.trace_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
