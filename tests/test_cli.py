import os

from pytradingview.__main__ import resolve_auth_token


def test_resolve_auth_token_from_primary_env(monkeypatch):
    monkeypatch.setenv("PYTRADINGVIEW_AUTH_TOKEN", "env-token")
    monkeypatch.delenv("TV_AUTH_TOKEN", raising=False)

    assert resolve_auth_token("cli-token") == "env-token"


def test_resolve_auth_token_from_secondary_env(monkeypatch):
    monkeypatch.delenv("PYTRADINGVIEW_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("TV_AUTH_TOKEN", "tv-env-token")

    assert resolve_auth_token("cli-token") == "tv-env-token"


def test_resolve_auth_token_falls_back_to_cli(monkeypatch):
    monkeypatch.delenv("PYTRADINGVIEW_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TV_AUTH_TOKEN", raising=False)

    assert resolve_auth_token("cli-token") == "cli-token"


def test_resolve_auth_token_none_when_unset(monkeypatch):
    monkeypatch.delenv("PYTRADINGVIEW_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TV_AUTH_TOKEN", raising=False)

    assert resolve_auth_token(None) is None
