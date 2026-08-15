import mingagent.history as history


def test_save_and_load_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(history, "SESSIONS_DIR", tmp_path / "sessions")

    events = [{"type": "tool", "action": "cmd", "output": "x" * 100}]
    messages = [{"role": "user", "content": "hi"}]
    history.save_history_entry("任务", "completed", "摘要", events=events, messages=messages)

    data = history.load_history()
    assert len(data) == 1
    assert data[0]["snapshot"] is True
    assert data[0]["title"] == "任务"

    snapshot = history.load_snapshot(data[0]["id"])
    assert snapshot is not None
    assert snapshot["events"] == events
    assert snapshot["messages"] == messages


def test_load_snapshot_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(history, "SESSIONS_DIR", tmp_path / "sessions")
    assert history.load_snapshot("nope") is None


def test_load_snapshot_bad_file(monkeypatch, tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    (sessions / "1.json").write_text("{bad", encoding="utf-8")
    monkeypatch.setattr(history, "SESSIONS_DIR", sessions)
    assert history.load_snapshot("1") is None
