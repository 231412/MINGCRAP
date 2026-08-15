from mingagent.tools import ToolResult, _decode_bytes, _limit_output, truncate_for_context


def test_decode_bytes_gbk():
    assert _decode_bytes("中文".encode("gbk")) == "中文"


def test_decode_bytes_utf8():
    assert _decode_bytes("中文".encode("utf-8")) == "中文"


def test_decode_bytes_ascii():
    assert _decode_bytes(b"AB") == "AB"


def test_decode_bytes_fallback():
    # 非法序列最终走 errors="replace"，不会抛异常
    assert isinstance(_decode_bytes(b"\xff\xfe\x81"), str)


def test_limit_output():
    text, truncated = _limit_output("x" * 100)
    assert not truncated
    text, truncated = _limit_output("x" * 13000)
    assert truncated
    assert "截断" in text
    assert len(text) <= 13000


def test_truncate_for_context():
    assert truncate_for_context("short") == "short"
    result = truncate_for_context("x" * 7000)
    assert "截断" in result


def test_tool_result_output_combines_stderr():
    result = ToolResult("cmd", "dir", True, "out", "err", 0.1)
    assert result.output == "out\nerr"
    assert result.cancelled is False
