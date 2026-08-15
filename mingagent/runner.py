"""后台 Agent 循环：在独立线程中执行 LLM 决策与工具调用。

与 UI 通过 run_state 共享内存通信：
- inbox：worker → UI 的事件队列（queue.Queue）；
- live：当前步骤的实时状态（流式文本 / 正在执行的工具）；
- pending：待用户确认的危险操作及其 decision Event；
- cancel：用户请求停止的事件（可中断正在执行的命令）。

本模块严禁调用任何 streamlit API，保证可在工作线程中安全运行。
"""

import threading
import time

from .history import save_history_entry
from .llm import (
    build_system_prompt,
    call_llm,
    parse_response,
    prepare_context,
    wrap_observation,
)
from .memory import commit_expertise, load_expertise
from .security import assess_risk, audit_log
from .tools import execute_cmd, execute_python, truncate_for_context, web_search

MAX_PARSE_FAILURES = 3
SNAPSHOT_EVENT_LIMIT = 15
SNAPSHOT_OUTPUT_CHARS = 1500
SNAPSHOT_MESSAGE_CHARS = 2000


def _push(rs: dict, event: dict) -> None:
    rs["inbox"].put(event)
    rs["log"].append(event)


def _snapshot_events(events: list[dict]) -> list[dict]:
    out = []
    for event in events[-SNAPSHOT_EVENT_LIMIT:]:
        copy = dict(event)
        if copy.get("type") == "tool":
            copy["output"] = str(copy.get("output", ""))[:SNAPSHOT_OUTPUT_CHARS]
        out.append(copy)
    return out


def _snapshot_messages(messages: list[dict]) -> list[dict]:
    return [
        {
            "role": item.get("role"),
            "content": str(item.get("content", ""))[:SNAPSHOT_MESSAGE_CHARS],
        }
        for item in messages[-24:]
    ]


def _finish(rs: dict, status: str, summary: str, messages: list[dict]) -> None:
    rs["live"]["text"] = ""
    rs["live"]["tool"] = None
    rs["live"]["step"] = 0
    save_history_entry(
        rs["task"],
        status,
        summary,
        events=_snapshot_events(rs.get("log", [])),
        messages=_snapshot_messages(messages),
    )
    rs["running"] = False


def _execute_action(parsed: dict, search_key: str, cancel_event):
    action = parsed["action"]
    payload = parsed["payload"]
    if action == "cmd":
        return execute_cmd(payload, cancel_event)
    if action == "python":
        return execute_python(payload, cancel_event)
    if action == "search":
        return web_search(payload, search_key)
    return None


def _await_decision(rs: dict, parsed: dict, raw: str, reason: str, safe_mode: bool, cancel):
    """挂起等待用户在 UI 上确认 / 取消危险操作。"""
    event = threading.Event()
    rs["pending"] = {
        "parsed": parsed,
        "raw": raw,
        "reason": reason,
        "safe_mode": safe_mode,
        "decision": None,
        "event": event,
    }
    while not event.is_set() and not cancel.is_set():
        time.sleep(0.1)
    decision = rs["pending"].get("decision") if event.is_set() else None
    rs["pending"] = None
    audit_log(
        {
            "event": "decision",
            "decision": decision if decision is not None else "stopped",
            "task": rs["task"],
            "action": parsed["action"],
            "payload": parsed["payload"][:2000],
        }
    )
    return decision


def agent_loop_worker(rs: dict, prompt: str, cfg: dict, resume_messages=None) -> None:
    cancel = rs["cancel"]
    messages: list[dict] = list(resume_messages or [])
    messages.append({"role": "user", "content": prompt})
    candidates: list[str] = []
    expertise = load_expertise()
    system_prompt = build_system_prompt(
        cfg.get("env_info", ""),
        expertise,
        cfg.get("search_enabled", True),
    )
    step_limit = int(cfg.get("step_limit", 10))
    step = 0
    parse_failures = 0

    try:
        while step < step_limit and not cancel.is_set():
            step += 1
            rs["live"]["text"] = ""
            rs["live"]["tool"] = None
            rs["live"]["step"] = step

            def on_chunk(text: str) -> None:
                rs["live"]["text"] += text

            try:
                raw = call_llm(
                    cfg["api_key"],
                    cfg["base_url"],
                    cfg["model"],
                    prepare_context(system_prompt, messages),
                    on_chunk=on_chunk,
                )
            except Exception as exc:
                _push(rs, {"type": "final", "content": f"LLM 调用失败：{exc}", "kind": "error"})
                _finish(rs, "error", f"LLM 调用失败：{exc}", messages)
                return

            rs["live"]["text"] = ""
            parsed = parse_response(raw)
            if parsed["thought"]:
                _push(rs, {"type": "thought", "content": parsed["thought"]})

            action = parsed["action"]
            payload = str(parsed.get("payload", "")).strip()

            if action == "final" and payload:
                messages.append({"role": "assistant", "content": raw})
                commit_expertise(rs["task"], candidates)
                _push(rs, {"type": "final", "content": payload, "kind": "success"})
                _finish(rs, "completed", payload, messages)
                return

            if action in {"cmd", "python", "search"} and not payload:
                parse_failures += 1
                if parse_failures >= MAX_PARSE_FAILURES:
                    _push(
                        rs,
                        {
                            "type": "final",
                            "content": "模型连续多次输出无效格式，任务终止。",
                            "kind": "error",
                        },
                    )
                    _finish(rs, "error", "模型连续多次输出无效格式，任务终止。", messages)
                    return
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": wrap_observation(
                            "[system] 你的输出无法解析：payload 为空。请严格按协议只输出一个 JSON 对象。"
                        ),
                    }
                )
                continue

            parse_failures = 0

            verdict, reason = assess_risk(action, payload, cfg.get("safe_mode", True))

            if action in {"cmd", "python"} and verdict == "confirm":
                audit_log(
                    {
                        "event": "risk",
                        "task": rs["task"],
                        "action": action,
                        "payload": payload[:2000],
                        "verdict": verdict,
                        "reason": reason,
                        "safe_mode": cfg.get("safe_mode", True),
                    }
                )
                decision = _await_decision(
                    rs, parsed, raw, reason, cfg.get("safe_mode", True), cancel
                )
                if cancel.is_set():
                    _push(rs, {"type": "final", "content": "任务已由用户停止。", "kind": "stopped"})
                    _finish(rs, "stopped", "任务已由用户停止。", messages)
                    return
                if decision is None:
                    _push(
                        rs,
                        {
                            "type": "tool",
                            "action": action,
                            "payload": payload,
                            "status": "error",
                            "output": "用户已拒绝执行该操作",
                            "elapsed": 0.0,
                            "truncated": False,
                        },
                    )
                    messages.append({"role": "assistant", "content": raw})
                    messages.append(
                        {
                            "role": "user",
                            "content": wrap_observation(
                                f"[{action}] 用户拒绝执行该操作，请调整方案。"
                            ),
                        }
                    )
                    continue

            rs["live"]["tool"] = action
            result = _execute_action(parsed, cfg.get("search_key", ""), cancel)
            rs["live"]["tool"] = None

            if result is None:
                _push(
                    rs,
                    {
                        "type": "final",
                        "content": "模型返回了无法识别的动作，请检查输出格式。",
                        "kind": "error",
                    },
                )
                _finish(rs, "error", "模型返回了无法识别的动作。", messages)
                return

            if result.cancelled:
                _push(
                    rs,
                    {
                        "type": "tool",
                        "action": action,
                        "payload": payload,
                        "status": "error",
                        "output": "已由用户停止",
                        "elapsed": result.elapsed,
                        "truncated": False,
                    },
                )
                audit_log(
                    {
                        "event": "execute",
                        "task": rs["task"],
                        "action": action,
                        "payload": payload[:2000],
                        "ok": False,
                        "cancelled": True,
                    }
                )
                _push(rs, {"type": "final", "content": "任务已由用户停止。", "kind": "stopped"})
                _finish(rs, "stopped", "任务已由用户停止。", messages)
                return

            status = "success" if result.ok else "error"
            _push(
                rs,
                {
                    "type": "tool",
                    "action": action,
                    "payload": payload,
                    "status": status,
                    "output": result.output,
                    "elapsed": result.elapsed,
                    "truncated": result.truncated,
                },
            )
            messages.append({"role": "assistant", "content": raw})
            messages.append(
                {
                    "role": "user",
                    "content": wrap_observation(
                        truncate_for_context(f"[{action}] {status}\n{result.output}")
                    ),
                }
            )
            audit_log(
                {
                    "event": "execute",
                    "task": rs["task"],
                    "action": action,
                    "payload": payload[:2000],
                    "ok": result.ok,
                    "elapsed": round(result.elapsed, 3),
                    "verdict": verdict,
                    "reason": reason,
                }
            )
            if action == "cmd" and result.ok:
                candidates.append(payload)

        if cancel.is_set():
            _push(rs, {"type": "final", "content": "任务已由用户停止。", "kind": "stopped"})
            _finish(rs, "stopped", "任务已由用户停止。", messages)
        else:
            _push(
                rs,
                {
                    "type": "final",
                    "content": f"已达最大步数上限（{step_limit}），任务已停止。",
                    "kind": "stopped",
                },
            )
            _finish(rs, "stopped", f"已达最大步数上限（{step_limit}）。", messages)
    except Exception as exc:
        _push(rs, {"type": "final", "content": f"内部错误：{exc}", "kind": "error"})
        _finish(rs, "error", f"内部错误：{exc}", messages)
