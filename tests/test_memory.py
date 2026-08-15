import mingagent.memory as memory


def test_sanitize_command():
    assert memory.sanitize_command("  del   C:\\Users\\me\\a.txt  ") == "del <path>"
    assert memory.sanitize_command('del "C:\\Program Files\\x"') == "del <path>"
    assert memory.sanitize_command("dir") == "dir"


def test_commit_expertise_dedupes_and_sanitizes(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "EXPERTISE_FILE", tmp_path / "expertise.json")
    memory.commit_expertise(
        "清理",
        [
            "del C:\\Users\\me\\a.txt",
            "del C:\\Users\\me\\a.txt",  # 重复
            "del D:\\data\\b.txt",      # 脱敏后与第一条归一化相同，被去重
            "dir",                      # 正常
            "x",                        # 太短，跳过
        ],
    )
    data = memory.load_expertise()
    cmds = [item["cmd"] for item in data]
    assert len(data) == 2
    assert cmds == ["del <path>", "dir"]  # 按时间倒序，同批提交的保持稳定
    assert all("ts" in item for item in data)


def test_delete_expertise(monkeypatch, tmp_path):
    monkeypatch.setattr(memory, "EXPERTISE_FILE", tmp_path / "expertise.json")
    memory.commit_expertise("t", ["dir", "where python"])
    memory.delete_expertise("dir")
    data = memory.load_expertise()
    assert len(data) == 1
    assert data[0]["cmd"] == "where python"


def test_load_expertise_tolerates_bad_file(monkeypatch, tmp_path):
    path = tmp_path / "expertise.json"
    monkeypatch.setattr(memory, "EXPERTISE_FILE", path)
    path.write_text("{bad json", encoding="utf-8")
    assert memory.load_expertise() == []
