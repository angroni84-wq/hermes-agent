from __future__ import annotations

import pytest

from browser_connect import DEFAULT_BROWSER_CDP_URL, normalize_browser_connect_target


def test_blank_target_uses_default():
    assert normalize_browser_connect_target("") == DEFAULT_BROWSER_CDP_URL


def test_comet_alias_resolves_to_default_local_cdp():
    assert normalize_browser_connect_target("comet") == DEFAULT_BROWSER_CDP_URL


def test_numeric_port_resolves_to_localhost_http_url():
    assert normalize_browser_connect_target("9333") == "http://127.0.0.1:9333"


def test_host_port_without_scheme_gets_http_prefix():
    assert normalize_browser_connect_target("127.0.0.1:9222") == "http://127.0.0.1:9222"


def test_invalid_alias_raises_helpful_error():
    with pytest.raises(ValueError, match="Unsupported browser target"):
        normalize_browser_connect_target("banana")
