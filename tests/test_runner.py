import json
import queue
import threading

import mingagent.runner as runner


def make_rs():
    return {
        "task": "测试任务",
        "events": [],
        "log": [],
        "inbox": queue.Queue(),
        "live": {"text": "", "tool": None, "step": 0},
        "pending": None,
        "cancel": threading.Event(),
        "running": True,
        "rerun_done": False,
        "toasted": False,
        "limit": 5,
    }


def make_cfg(**overrides):
    cfg = {
        "api_key": "x",
        "base_url": "http://x",
        "model": "m",
        "search_key": "",
        "search_enabled": True,
        "safe_mode": True,
        "step_limit": 5,
        "env_info": "python",
    }
    cfg.update(overrides)
    return cfg


def drain(rs):
    while True:
        try:
            rs["events"].append(rs["inbox"].get_nowait())
        except queue.Empty:
            break


def test_worker_completes_and_commits_expertise(monkeypatch):
    committed = {}
    monkeypatch.setattr(runner, "save_history_entry", lambda *a, **k: None)
    monkeypatch.setattr(runner, "audit_log", lambda *a, **k: None)

    def fake_commit(task, commands):
        committed["task"] = task
        committed["commands"] = commands

    monkeypatch.setattr(runner, "commit_expertise", fake_commit)

    responses = iter(
        [
            json.dumps({"thought": "t1", "action": "cmd", "payload": "echo hi"}),
            json.dumps({"thought": "t2", "action": "final", "payload": "完成"}),
        ]
    )

    def fake_llm(api_key, base_url, model, messages, on_chunk=None, retries=3):
        return next(responses)

    monkeypatch.setattr(runner, "call_llm", fake_llm)

    rs = make_rs()
    runner.agent_loop_worker(rs, "测试任务", make_cfg())
    drain(rs)
    finals = [e for e in rs["events"] if e["type"] == "final"]
    assert not rs["running"]
    assert finals[-1]["kind"] == "success"
    # 经验只在任务成功后提交
    assert committed == {"task": "测试任务", "commands": ["echo hi"]}


def test_worker_failure_does_not_commit_expertise(monkeypatch):
    committed = []
    monkeypatch.setattr(runner, "save_history_entry", lambda *a, **k: None)
    monkeypatch.setattr(runner, "audit_log", lambda *a, **k: None)
    monkeypatch.setattr(runner, "commit_expertise", lambda task, cmds: committed.extend(cmds))

    bad = json.dumps({"action": "cmd", "payload": ""})
    monkeypatch.setattr(runner, "call_llm", lambda *a, **k: bad)

    rs = make_rs()
    runner.agent_loop_worker(rs, "t", make_cfg())
    drain(rs)
    finals = [e for e in rs["events"] if e["type"] == "final"]
    assert finals[-1]["kind"] == "error"
    assert committed == []


def test_worker_saves_snapshot(monkeypatch):
    saved = {}
    monkeypatch.setattr(runner, "audit_log", lambda *a, **k: None)
    monkeypatch.setattr(runner, "commit_expertise", lambda *a, **k: None)

    def fake_save(title, status, summary, events=None, messages=None):
        saved["events"] = events
        saved["messages"] = messages

    monkeypatch.setattr(runner, "save_history_entry", fake_save)

    responses = iter(
        [
            json.dumps({"action": "cmd", "payload": "echo " + "x" * 3000}),
            json.dumps({"action": "final", "payload": "ok"}),
        ]
    )
    monkeypatch.setattr(runner, "call_llm", lambda *a, **k: next(responses))

    rs = make_rs()
    runner.agent_loop_worker(rs, "t", make_cfg())
    drain(rs)
    # 快照中工具输出被截断
    tool_events = [e for e in saved["events"] if e["type"] == "tool"]
    assert tool_events
    assert len(tool_events[0]["output"]) <= 1500
    assert saved["messages"]


def test_worker_resume_messages_are_seeded(monkeypatch):
    seen_context = {}
    monkeypatch.setattr(runner, "save_history_entry", lambda *a, **k: None)
    monkeypatch.setattr(runner, "audit_log", lambda *a, **k: None)
    monkeypatch.setattr(runner, "commit_expertise", lambda *a, **k: None)

    def fake_llm(api_key, base_url, model, messages, on_chunk=None, retries=3):
        seen_context["roles"] = [m["role"] for m in messages]
        return json.dumps({"action": "final", "payload": "ok"})

    monkeypatch.setattr(runner, "call_llm", fake_llm)

    rs = make_rs()
    resume = [{"role": "user", "content": "旧问题"}, {"role": "assistant", "content": "旧回答"}]
    runner.agent_loop_worker(rs, "新指令", make_cfg(), resume_messages=resume)
    drain(rs)
    # prepare_context 会在最前加上 system，随后是续接消息和新指令
    assert seen_context["roles"][:4] == ["system", "user", "assistant", "user"]
    assert seen_context["roles"][-1] == "user"
