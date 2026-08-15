import pytest

from mingagent.security import (
    analyze_python,
    assess_risk,
    detect_dangerous_cmd,
    matches_safe_cmd,
)


@pytest.mark.parametrize(
    "action,payload,mode,expected",
    [
        # Python 危险调用
        ('python', 'import os\nos.remove("x.txt")', True, "confirm"),
        ('python', 'from os import remove\nremove("x")', True, "confirm"),
        ('python', 'import subprocess\nsubprocess.run("dir")', False, "confirm"),
        ('python', 'getattr(os, "re"+"move")("x")', True, "confirm"),
        ('python', 'eval("1+1")', False, "confirm"),
        ('python', 'shutil.rmtree("x")', True, "confirm"),
        # Python 只读 / 写操作
        ('python', 'print("hello")', True, "safe"),
        ('python', 'os.getcwd(); os.listdir(".")', True, "safe"),
        ('python', 'open("out.txt","w").write("hi")', True, "confirm"),  # 安全模式写操作
        ('python', 'open("out.txt","w").write("hi")', False, "safe"),   # 自动模式放行
        # cmd 危险规则
        ('cmd', 'rd /s /q D:\\test', True, "confirm"),
        ('cmd', 'dir & del a.txt', True, "confirm"),
        ('cmd', 'del C:\\x.txt', False, "confirm"),
        # cmd 白名单 / 安全模式
        ('cmd', 'dir', True, "safe"),
        ('cmd', 'wmic cpu get loadpercentage', True, "safe"),
        ('cmd', 'powershell -Command "Get-ChildItem"', True, "safe"),
        ('cmd', 'mkdir newfolder', True, "confirm"),
        ('cmd', 'mkdir newfolder', False, "safe"),
        ('cmd', 'dir > out.txt', True, "confirm"),
        # 搜索永远安全
        ('search', 'python', True, "safe"),
    ],
)
def test_assess_risk(action, payload, mode, expected):
    verdict, _ = assess_risk(action, payload, mode)
    assert verdict == expected


def test_analyze_python_detects_os_remove():
    danger, _ = analyze_python('import os\nos.remove("x")')
    assert "os.remove" in danger


def test_analyze_python_detects_open_write():
    _, mutation = analyze_python('open("f", "w").write("x")')
    assert any("open" in item for item in mutation)


def test_analyze_python_read_only_is_safe():
    danger, mutation = analyze_python('import os\nos.listdir(".")')
    assert not danger and not mutation


def test_analyze_python_syntax_error_is_harmless():
    danger, mutation = analyze_python("this is not valid python !!!")
    assert not danger and not mutation


def test_detect_dangerous_cmd_alias_and_chain():
    assert detect_dangerous_cmd("rd /s /q C:\\x")
    assert detect_dangerous_cmd("dir & del a.txt")
    assert detect_dangerous_cmd("echo hi") is None


def test_matches_safe_cmd():
    assert matches_safe_cmd("dir")
    assert matches_safe_cmd("git status")
    assert not matches_safe_cmd("mkdir x")
    assert not matches_safe_cmd("dir > out.txt")
    assert not matches_safe_cmd("dir & del a.txt")
