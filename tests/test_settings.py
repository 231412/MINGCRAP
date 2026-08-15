import mingagent.settings as settings


def test_save_load_roundtrip(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SETTINGS_FILE", tmp_path / "settings.json")
    settings.save_settings("light", "#2DD4BF")
    assert settings.load_settings() == {"theme": "light", "accent": "#2DD4BF"}
    settings.save_settings("dark", "#F5F5F5")
    assert settings.load_settings() == {"theme": "dark", "accent": "#F5F5F5"}


def test_load_settings_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "SETTINGS_FILE", tmp_path / "missing.json")
    assert settings.load_settings() == {"theme": "dark", "accent": "#F5F5F5"}


def test_load_settings_bad_json(monkeypatch, tmp_path):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_FILE", path)
    path.write_text("{bad", encoding="utf-8")
    assert settings.load_settings() == {"theme": "dark", "accent": "#F5F5F5"}


def test_load_settings_rejects_unknown_values(monkeypatch, tmp_path):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_FILE", path)
    path.write_text('{"theme": "neon", "accent": "#123456"}', encoding="utf-8")
    assert settings.load_settings() == {"theme": "dark", "accent": "#F5F5F5"}
