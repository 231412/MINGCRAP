import mingagent.config as config


def test_data_dir_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("MINGAGENT_DATA_DIR", str(tmp_path / "data"))
    assert config._data_dir() == tmp_path / "data"


def test_data_dir_dev_default_is_root(monkeypatch):
    monkeypatch.delenv("MINGAGENT_DATA_DIR", raising=False)
    monkeypatch.setattr(config, "FROZEN", False)
    assert config._data_dir() == config.ROOT_DIR


def test_data_dir_frozen_uses_appdata(monkeypatch, tmp_path):
    monkeypatch.delenv("MINGAGENT_DATA_DIR", raising=False)
    monkeypatch.setattr(config, "FROZEN", True)
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert config._data_dir() == tmp_path / "MINGAGENT"
    assert (tmp_path / "MINGAGENT").exists()  # 目录自动创建


def test_data_files_derived_from_data_dir():
    assert config.EXPERTISE_FILE == config.DATA_DIR / "expertise.json"
    assert config.HISTORY_FILE == config.DATA_DIR / "history.json"
    assert config.AUDIT_FILE == config.DATA_DIR / "audit.jsonl"
    assert config.SESSIONS_DIR == config.DATA_DIR / "sessions"


def test_work_dir_dev_is_root(monkeypatch):
    monkeypatch.setattr(config, "FROZEN", False)
    assert config.WORK_DIR == config.ROOT_DIR
