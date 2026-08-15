from mingagent.llm import parse_response, prepare_context, wrap_observation


def test_parse_plain_json():
    parsed = parse_response('{"thought":"t","action":"cmd","payload":"dir"}')
    assert parsed["action"] == "cmd"
    assert parsed["payload"] == "dir"
    assert parsed["thought"] == "t"


def test_parse_fenced_json():
    parsed = parse_response('```json\n{"action":"final","payload":"ok"}\n```')
    assert parsed["action"] == "final"
    assert parsed["payload"] == "ok"


def test_parse_json_embedded_in_text():
    parsed = parse_response('好的，接下来：\n{"action":"search","payload":"python"}\n以上。')
    assert parsed["action"] == "search"


def test_parse_legacy_run_cmd():
    parsed = parse_response("RUN_CMD: dir /b")
    assert parsed["action"] == "cmd"
    assert parsed["payload"] == "dir /b"


def test_parse_legacy_finish():
    parsed = parse_response("FINISH: 任务完成")
    assert parsed["action"] == "final"


def test_parse_unknown_action_falls_back_to_final():
    parsed = parse_response('{"action":"hack","payload":"x"}')
    assert parsed["action"] == "final"


def test_parse_garbage_becomes_final():
    parsed = parse_response("随便说点什么")
    assert parsed["action"] == "final"
    assert parsed["payload"] == "随便说点什么"


def test_wrap_observation():
    assert wrap_observation("abc") == "<tool_output>\nabc\n</tool_output>"


def test_prepare_context_windows_messages():
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
    prepared = prepare_context("system", messages)
    assert prepared[0] == {"role": "system", "content": "system"}
    assert len(prepared) == 25  # system + 最近 24 条
    assert prepared[-1]["content"] == "msg 29"
