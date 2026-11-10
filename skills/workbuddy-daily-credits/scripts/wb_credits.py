#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WorkBuddy 每日积分一键跑：签到 + 派猫猫旅行 + 开盲盒。

跨平台（Windows / macOS / Linux），纯 Python 标准库，零第三方依赖。

它做三件事：
  ① 签到        POST /v2/billing/meter/daily-checkin（幂等：当天已签自动跳过）
  ② 派猫猫旅行   先领已到达的奖励，再派新的一趟（达每日上限则跳过）
  ③ 开盲盒      GET 能量/单价 → 能量够才 POST /activity/growth/buddy/open

安全边界：
  - 只读取本机 WorkBuddy 的登录态，绝不打印、绝不上传 accessToken；
  - 写操作只碰上面三个接口，不调用兑换、抽奖等任何其他写接口；
  - 能量不足一次成本时，绝不发送开箱请求；
  - --dry-run 预览模式只读不写。

用法：
  python wb_credits.py                # 真跑三件事
  python wb_credits.py --dry-run      # 只预览，不提交任何写请求
  python wb_credits.py --no-box       # 跳过盲盒
  python wb_credits.py --max-box 1    # 本次最多开 1 个盲盒
  python wb_credits.py --json         # 机器可读输出
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import buddy_station as bs
except Exception as exc:  # noqa: BLE001
    print("缺少依赖脚本 scripts/buddy_station.py：%s" % exc)
    raise SystemExit(1)

OPEN_PATH = "/activity/growth/buddy/open"
DEFAULT_CFG = {"checkin": True, "travel": True, "blindbox": True, "max_box_per_run": 2}


def load_cfg(path=None):
    cfg = dict(DEFAULT_CFG)
    p = path or os.path.join(PKG_ROOT, "config.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for k, v in raw.items():
            if not str(k).startswith("_"):
                cfg[k] = v
    except FileNotFoundError:
        pass
    except Exception as exc:  # noqa: BLE001
        print("[warn] config.json 解析失败，改用默认值：%s" % exc)
    return cfg


def read_energy(token):
    d = bs._travel_get(token, bs.GROWTH_ENERGY_PATH) or {}
    return d.get("balance")


def read_cost(token):
    d = bs._travel_get(token, bs.BUDDY_QUOTA_PATH) or {}
    try:
        return int(d.get("cost_per_open") or 10)
    except Exception:  # noqa: BLE001
        return 10


def run_box(token, max_open, dry):
    out = {"energy_before": None, "cost": None, "affordable": 0,
           "opened": 0, "energy_after": None, "message": ""}
    energy = read_energy(token)
    cost = read_cost(token)
    out["energy_before"], out["cost"] = energy, cost

    if energy is None:
        out["message"] = "读不到能量余额，未开箱"
        return out

    try:
        affordable = max(0, int(energy) // int(cost))
    except Exception:  # noqa: BLE001
        affordable = 0
    out["affordable"] = affordable

    if affordable <= 0:
        out["message"] = "能量 %s / 每次 %s，不够开一次，未开箱" % (energy, cost)
        return out

    count = min(int(max_open), affordable)
    if dry:
        out["message"] = "[预览] 能量 %s，够开 %d 次，计划开 %d 个（未提交）" % (energy, affordable, count)
        return out

    st, body = bs.api_call(bs.TRAVEL_DOMAIN, token, OPEN_PATH, "POST", {"count": count})
    code = body.get("code") if isinstance(body, dict) else None
    if st != 200 or code != 0:
        msg = (body or {}).get("msg") if isinstance(body, dict) else ""
        out["message"] = "开箱失败：HTTP %s code=%s msg=%s" % (st, code, msg)
        out["raw"] = body
        return out

    data = body.get("data")
    opened = count
    if isinstance(data, dict):
        items = data.get("buddies") or data.get("list") or data.get("items")
        if isinstance(items, list):
            opened = len(items)
    out["opened"] = opened
    out["energy_after"] = read_energy(token)
    out["message"] = "开了 %d 个盲盒，能量 %s → %s" % (opened, energy, out["energy_after"])
    out["raw"] = data
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="WorkBuddy 每日积分：签到 + 派猫猫 + 开盲盒")
    ap.add_argument("--dry-run", action="store_true", help="只预览，不提交任何写请求")
    ap.add_argument("--no-box", action="store_true", help="跳过盲盒")
    ap.add_argument("--max-box", type=int, default=None, help="本次最多开几个盲盒（默认取 config.json）")
    ap.add_argument("--channel", default="auto", choices=["auto", "local", "web"], help="登录态通道")
    ap.add_argument("--config", default=None, help="配置文件路径")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    result = {"dry_run": args.dry_run, "channel": None,
              "checkin": None, "travel": None, "blindbox": None, "summary": {}}

    # ---------- 取登录态 ----------
    try:
        token, domain, headers = bs._resolve_auth(args.channel)
    except Exception as exc:  # noqa: BLE001
        msg = ("登录态不可用：%s\n"
               "  · Windows：确认 WorkBuddy 客户端已登录（通道 A 零配置）\n"
               "  · macOS：若提示无法解密，用 scripts/web_auth.py 走一次网页授权"
               % exc)
        print(json.dumps({"error": msg}, ensure_ascii=False) if args.json else msg)
        return 2
    result["channel"] = "cookie" if headers else "bearer"

    # ---------- ① 签到 ----------
    if cfg.get("checkin", True):
        if args.dry_run:
            try:
                st = bs.fetch_status(domain, token)
                result["checkin"] = {"action": "preview",
                                     "message": "今日已签到" if st.get("today_checked_in") else "今日未签到，会提交签到"}
            except Exception as exc:  # noqa: BLE001
                result["checkin"] = {"action": "failed", "message": "查询失败：%s" % exc}
        else:
            result["checkin"] = bs.do_checkin(domain, token)

    # ---------- ② 派猫猫旅行 ----------
    if cfg.get("travel", True):
        try:
            if args.dry_run:
                raw = bs.fetch_travel(token)
                tv = bs.parse_travel(raw) or {}
                result["travel"] = {"success": True, "state": tv.get("state_text") or tv.get("state"),
                                    "log": ["[预览] 不提交领取/派遣"], "preview": True}
            else:
                result["travel"] = bs.travel_auto(token)
        except Exception as exc:  # noqa: BLE001
            result["travel"] = {"success": False, "log": ["旅行任务异常：%s" % exc]}

    # ---------- ③ 开盲盒 ----------
    if cfg.get("blindbox", True) and not args.no_box:
        max_box = args.max_box if args.max_box is not None else int(cfg.get("max_box_per_run", 2))
        result["blindbox"] = run_box(token, max_box, args.dry_run)

    # ---------- 汇总（只读） ----------
    try:
        st = bs.fetch_status(domain, token)
        result["summary"] = {"total_credits": st.get("total_credits"),
                             "streak_days": st.get("streak_days"),
                             "today_checked_in": st.get("today_checked_in")}
    except Exception:  # noqa: BLE001
        pass

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    # ---------- 中文简报 ----------
    title = "== WorkBuddy 每日积分 =="
    if args.dry_run:
        title = "== WorkBuddy 每日积分（预览模式，未提交写请求） =="
    print(title)

    ck = result["checkin"] or {}
    if ck:
        print("① 签到：%s" % (ck.get("message") or ck.get("action") or "无返回"))

    tv = result["travel"] or {}
    if tv:
        state = tv.get("state") or "-"
        logs = " → ".join([x for x in (tv.get("log") or []) if x])
        print("② 猫猫：状态 %s｜%s" % (state, logs or "无动作"))

    bx = result["blindbox"] or {}
    if bx:
        print("③ 盲盒：%s" % (bx.get("message") or "未执行"))

    s = result["summary"] or {}
    if s:
        print("-" * 40)
        print("积分余额：%s｜连续登录：%s 天｜今日已签到：%s"
              % (s.get("total_credits"), s.get("streak_days"), s.get("today_checked_in")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
