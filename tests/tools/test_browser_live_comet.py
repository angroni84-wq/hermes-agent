from unittest.mock import MagicMock, patch, mock_open
import json
import subprocess


import tools.browser_tool as browser_tool


def test_open_local_comet_tab_uses_about_blank(monkeypatch):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured['cmd'] = cmd
        captured['kwargs'] = kwargs
        class Result:
            returncode = 0
        return Result()

    monkeypatch.setattr(browser_tool.subprocess, 'run', fake_run)

    browser_tool._open_local_comet_tab()

    assert captured['cmd'][0] == 'osascript'
    assert 'about:blank' in captured['cmd'][2]


def test_agent_browser_cdp_url_uses_http_discovery_for_local_comet(monkeypatch):
    session_info = {
        'cdp_url': 'ws://127.0.0.1:9222/devtools/browser/test',
        'browser_target': 'comet',
        'features': {'cdp_override': True},
    }

    monkeypatch.setattr(browser_tool, '_is_local_comet_session', lambda session: True)
    monkeypatch.setattr(browser_tool, '_cdp_target_host_port', lambda url: ('127.0.0.1', 9222))

    assert browser_tool._agent_browser_cdp_url(session_info) == 'http://127.0.0.1:9222'


def test_is_local_comet_session_uses_detected_browser_alias(monkeypatch):
    session_info = {
        'cdp_url': 'ws://127.0.0.1:9222/devtools/browser/test',
        'browser_target': 'chrome',
        'features': {'cdp_override': True},
    }

    monkeypatch.setattr(browser_tool, '_detect_local_debug_browser_alias', lambda cdp_url: 'comet')

    assert browser_tool._is_local_comet_session(session_info) is True


def test_is_local_comet_session_rejects_non_comet_detected_browser(monkeypatch):
    session_info = {
        'cdp_url': 'ws://127.0.0.1:9222/devtools/browser/test',
        'browser_target': 'comet',
        'features': {'cdp_override': True},
    }

    monkeypatch.setattr(browser_tool, '_detect_local_debug_browser_alias', lambda cdp_url: 'chrome')

    assert browser_tool._is_local_comet_session(session_info) is False


def test_maybe_prepare_local_comet_launches_and_activates_for_open(monkeypatch):
    session_info = {
        "cdp_url": "http://127.0.0.1:9222",
        "browser_target": "comet",
    }
    calls: list[tuple[str, int | None]] = []
    port_checks = iter([False, True])

    monkeypatch.setattr(browser_tool, "_is_local_comet_session", lambda session: True)
    monkeypatch.setattr(browser_tool, "_cdp_target_host_port", lambda url: ("127.0.0.1", 9222))
    monkeypatch.setattr(browser_tool, "_is_port_open", lambda host, port, timeout=1.0: next(port_checks))
    monkeypatch.setattr(browser_tool, "_launch_local_comet_debug", lambda port: calls.append(("launch", port)) or True)
    monkeypatch.setattr(browser_tool, "_activate_local_comet", lambda: calls.append(("activate", None)))
    monkeypatch.setattr(browser_tool.time, "sleep", lambda *_args, **_kwargs: None)

    browser_tool._maybe_prepare_local_comet(session_info, "open")

    assert calls == [("launch", 9222), ("activate", None)]


def test_maybe_prepare_local_comet_activates_for_non_open_interactive_commands(monkeypatch):
    session_info = {
        "cdp_url": "http://127.0.0.1:9222",
        "browser_target": "comet",
    }
    calls: list[tuple[str, int | None]] = []

    monkeypatch.setattr(browser_tool, "_is_local_comet_session", lambda session: True)
    monkeypatch.setattr(browser_tool, "_cdp_target_host_port", lambda url: ("127.0.0.1", 9222))
    monkeypatch.setattr(browser_tool, "_is_port_open", lambda host, port, timeout=1.0: True)
    monkeypatch.setattr(browser_tool, "_activate_local_comet", lambda: calls.append(("activate", None)))

    browser_tool._maybe_prepare_local_comet(session_info, "click")

    assert calls == [("activate", None)]


def test_maybe_prepare_local_comet_skips_activation_for_snapshot(monkeypatch):
    session_info = {
        "cdp_url": "http://127.0.0.1:9222",
        "browser_target": "comet",
    }
    calls: list[tuple[str, int | None]] = []

    monkeypatch.setattr(browser_tool, "_is_local_comet_session", lambda session: True)
    monkeypatch.setattr(browser_tool, "_cdp_target_host_port", lambda url: ("127.0.0.1", 9222))
    monkeypatch.setattr(browser_tool, "_is_port_open", lambda host, port, timeout=1.0: True)
    monkeypatch.setattr(browser_tool, "_launch_local_comet_debug", lambda port: calls.append(("launch", port)) or True)
    monkeypatch.setattr(browser_tool, "_activate_local_comet", lambda: calls.append(("activate", None)))

    browser_tool._maybe_prepare_local_comet(session_info, "snapshot")

    assert calls == []


def test_run_browser_command_bootstraps_local_comet_via_connect(monkeypatch, tmp_path):
    session_info = {
        "session_name": "cdp_test",
        "cdp_url": "ws://127.0.0.1:9222/devtools/browser/test",
        "browser_target": "comet",
        "features": {"cdp_override": True},
    }
    captured_cmds = []

    def fake_popen(cmd, **kwargs):
        captured_cmds.append(cmd)
        return MagicMock()

    process_calls = []

    def fake_run_agent_browser_process(cmd_parts, browser_env, task_socket_dir, command_name, timeout):
        process_calls.append((command_name, cmd_parts))
        if command_name.startswith("connect_"):
            return {"returncode": -9, "stdout": "", "stderr": "", "timed_out": True}
        if command_name.startswith("ready_"):
            return {"returncode": 0, "stdout": '{"success":true,"data":{"url":"about:blank"}}', "stderr": "", "timed_out": False}
        return {"returncode": 0, "stdout": '{"success":true,"data":{"snapshot":"ok"}}', "stderr": "", "timed_out": False}

    monkeypatch.setattr(browser_tool, "_find_agent_browser", lambda: "/tmp/agent-browser")
    monkeypatch.setattr(browser_tool, "_get_session_info", lambda task_id: session_info)
    monkeypatch.setattr(browser_tool, "_socket_safe_tmpdir", lambda: str(tmp_path))
    monkeypatch.setattr(browser_tool, "_discover_homebrew_node_dirs", lambda: [])
    monkeypatch.setattr(browser_tool, "_maybe_prepare_local_comet", lambda session, command: None)
    monkeypatch.setattr(browser_tool, "_is_local_comet_session", lambda session: True)
    monkeypatch.setattr(browser_tool, "_agent_browser_connect_target", lambda session: "9222")
    monkeypatch.setattr(browser_tool, "_run_agent_browser_process", fake_run_agent_browser_process)

    with patch("subprocess.Popen", side_effect=fake_popen), \
         patch("os.open", return_value=99), \
         patch("os.close"), \
         patch("tools.interrupt.is_interrupted", return_value=False), \
         patch.dict("os.environ", {"PATH": "/usr/bin:/bin", "HOME": "/home/test"}, clear=True):
        result1 = browser_tool._run_browser_command("task-comet", "snapshot", ["-c"], timeout=20)
        result2 = browser_tool._run_browser_command("task-comet", "snapshot", ["-c"], timeout=20)

    assert result1["success"] is True
    assert result2["success"] is True
    connect_calls = [cmd for name, cmd in process_calls if name.startswith("connect_")]
    ready_calls = [cmd for name, cmd in process_calls if name.startswith("ready_")]
    snapshot_calls = [cmd for name, cmd in process_calls if name == "snapshot"]
    assert connect_calls[0][-2:] == ["connect", "9222"]
    assert ready_calls[0][-3:] == ["get", "url", "--json"]
    assert snapshot_calls[0][1:6] == ["--session", "cdp_test", "--json", "snapshot", "-c"]
    assert len(connect_calls) == 1
