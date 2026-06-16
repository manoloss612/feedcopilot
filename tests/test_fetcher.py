import httpx
from feedcopilot.db.repository import create_feed, list_items
from feedcopilot.db.session import get_session, init_db
from feedcopilot.rss import fetcher
from feedcopilot.rss.fetcher import (
    _resolve_proxy,
    fetch_enabled_feeds,
    normalize_items,
    parse_feed_content,
)

RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Feed</title>
    <link>https://example.com</link>
    <description>Example description</description>
    <item>
      <title>First Item</title>
      <link>https://example.com/first</link>
      <guid>first-guid</guid>
      <pubDate>Mon, 15 Jun 2026 08:00:00 GMT</pubDate>
      <description>First summary</description>
    </item>
  </channel>
</rss>
"""


def test_normalize_items_from_rss_xml():
    parsed = parse_feed_content(RSS_XML)

    items = normalize_items(parsed)

    assert len(items) == 1
    assert items[0].title == "First Item"
    assert items[0].guid == "first-guid"
    assert items[0].content_hash


def test_fetch_enabled_feeds_stores_new_items(tmp_path, monkeypatch):
    db_path = tmp_path / "feedcopilot.db"
    init_db(db_path)

    def fake_fetch_feed(url, timeout=20, user_agent="FeedCopilot/0.1", proxy=None):
        return parse_feed_content(RSS_XML)

    monkeypatch.setattr(fetcher, "fetch_feed", fake_fetch_feed)

    with get_session(db_path) as session:
        feed = create_feed(session, url="https://example.com/rss.xml")
        total, new = fetch_enabled_feeds(session)
        total_again, new_again = fetch_enabled_feeds(session)
        items = list_items(session, feed_id=feed.id)

    assert total == 1
    assert new == 1
    assert total_again == 1
    assert new_again == 0
    assert len(items) == 1
    assert items[0].title == "First Item"


def test_resolve_proxy_explicit_wins(monkeypatch):
    monkeypatch.setenv("HTTPS_PROXY", "http://from-env:1087")
    assert _resolve_proxy("http://from-arg:8080") == "http://from-arg:8080"


def test_resolve_proxy_falls_back_to_https_proxy(monkeypatch):
    monkeypatch.delenv("FEEDCOPILOT_PROXY", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", "http://from-https-env:1087")
    monkeypatch.setenv("HTTP_PROXY", "http://from-http-env:1087")
    assert _resolve_proxy(None) == "http://from-https-env:1087"


def test_resolve_proxy_falls_back_to_http_proxy(monkeypatch):
    monkeypatch.delenv("FEEDCOPILOT_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.setenv("HTTP_PROXY", "http://from-http-env:1087")
    assert _resolve_proxy(None) == "http://from-http-env:1087"


def test_resolve_proxy_empty_when_unset(monkeypatch):
    for var in ("FEEDCOPILOT_PROXY", "HTTPS_PROXY", "HTTP_PROXY"):
        monkeypatch.delenv(var, raising=False)
    assert _resolve_proxy(None) == ""
    assert _resolve_proxy("") == ""


def test_fetch_feed_uses_proxy_transport(monkeypatch):
    """When a proxy is set, httpx.Client must receive a transport with that proxy URL."""
    captured: dict = {}

    def fake_http_transport(proxy=None, **kwargs):
        captured["proxy"] = proxy
        captured["kwargs"] = kwargs
        # Return a sentinel — we never .open() the transport here.
        return object()

    monkeypatch.setattr(fetcher.httpx, "HTTPTransport", fake_http_transport)

    def fake_client(*args, **kwargs):
        captured["client_kwargs"] = kwargs
        class _C:
            def __enter__(self_inner):
                return self_inner
            def __exit__(self_inner, *exc):
                return False
            def get(self_inner, url):
                class _Resp:
                    status_code = 200
                    content = RSS_XML.encode("utf-8")
                    def raise_for_status(self_inner_inner):
                        return None
                return _Resp()
        return _C()

    monkeypatch.setattr(fetcher.httpx, "Client", fake_client)

    fetcher.fetch_feed("https://example.com/rss", proxy="http://127.0.0.1:1087")

    assert captured["proxy"] == "http://127.0.0.1:1087"
    assert captured["client_kwargs"].get("transport") is not None
    # timeout / follow_redirects / headers still passed through
    assert captured["client_kwargs"]["follow_redirects"] is True
    assert captured["client_kwargs"]["headers"]["User-Agent"] == "FeedCopilot/0.1"


def test_fetch_feed_no_proxy_means_no_transport_override(monkeypatch):
    """Without a proxy, httpx.Client must be constructed without a custom transport."""
    captured: dict = {}

    def fake_http_transport(*args, **kwargs):
        raise AssertionError("HTTPTransport must not be constructed when no proxy is set")

    monkeypatch.setattr(fetcher.httpx, "HTTPTransport", fake_http_transport)

    def fake_client(*args, **kwargs):
        captured.update(kwargs)
        class _C:
            def __enter__(self_inner):
                return self_inner
            def __exit__(self_inner, *exc):
                return False
            def get(self_inner, url):
                class _Resp:
                    status_code = 200
                    content = RSS_XML.encode("utf-8")
                    def raise_for_status(self_inner_inner):
                        return None
                return _Resp()
        return _C()

    monkeypatch.setattr(fetcher.httpx, "Client", fake_client)
    fetcher.fetch_feed("https://example.com/rss")
    assert "transport" not in captured
    assert captured["follow_redirects"] is True
    assert captured["headers"]["User-Agent"] == "FeedCopilot/0.1"


def test_fetch_feed_uses_env_proxy_when_no_arg(monkeypatch, tmp_path):
    """End-to-end: env var only → fetch_feed resolves and passes proxy through."""
    monkeypatch.delenv("FEEDCOPILOT_PROXY", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", "http://env-proxy:1087")
    captured: dict = {}

    def fake_http_transport(proxy=None, **kwargs):
        captured["proxy"] = proxy
        return object()

    def fake_client(*args, **kwargs):
        captured["client_kwargs"] = kwargs
        class _C:
            def __enter__(self_inner): return self_inner
            def __exit__(self_inner, *exc): return False
            def get(self_inner, url):
                class _Resp:
                    status_code = 200
                    content = RSS_XML.encode("utf-8")
                    def raise_for_status(self_inner_inner): return None
                return _Resp()
        return _C()

    monkeypatch.setattr(fetcher.httpx, "HTTPTransport", fake_http_transport)
    monkeypatch.setattr(fetcher.httpx, "Client", fake_client)
    fetcher.fetch_feed("https://example.com/rss")
    assert captured["proxy"] == "http://env-proxy:1087"
