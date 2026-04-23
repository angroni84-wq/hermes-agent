from __future__ import annotations

from urllib.parse import urlparse

DEFAULT_BROWSER_CDP_URL = "http://127.0.0.1:9222"
_BROWSER_TARGET_ALIASES = {
    "comet": DEFAULT_BROWSER_CDP_URL,
    "chrome": DEFAULT_BROWSER_CDP_URL,
}


def normalize_browser_connect_target(value: str | None) -> str:
    """Normalize a browser-connect target into a concrete CDP endpoint.

    Accepts:
    - empty string / None -> default local CDP endpoint
    - aliases like ``comet`` -> default local CDP endpoint
    - bare ports like ``9222`` -> ``http://127.0.0.1:9222``
    - bare host:port values -> ``http://host:port``
    - full http/https/ws/wss URLs -> unchanged

    Raises ``ValueError`` for unsupported bare words so we don't persist junk like
    ``BROWSER_CDP_URL=comet`` without normalizing it first.
    """
    raw = (value or "").strip()
    if not raw:
        return DEFAULT_BROWSER_CDP_URL

    alias = raw.lower()
    if alias in _BROWSER_TARGET_ALIASES:
        return _BROWSER_TARGET_ALIASES[alias]

    if raw.isdigit():
        return f"http://127.0.0.1:{raw}"

    if "://" not in raw:
        if raw.startswith(("localhost", "127.", "0.0.0.0", "[::1]")) or ":" in raw or "/" in raw:
            raw = f"http://{raw}"
        else:
            raise ValueError(
                f"Unsupported browser target {value!r}. Use 'comet', a port like '9222', or a CDP URL."
            )

    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https", "ws", "wss"} or not parsed.netloc:
        raise ValueError(
            f"Unsupported browser target {value!r}. Use 'comet', a port like '9222', or a CDP URL."
        )
    return raw


def browser_connect_port(value: str | None) -> int:
    """Return the TCP port implied by a browser-connect target."""
    normalized = normalize_browser_connect_target(value)
    parsed = urlparse(normalized)
    if parsed.port is not None:
        return parsed.port
    return 9222
