import pytest
from unittest.mock import MagicMock

from pytradingview.auth import TradingViewAuthError, get_auth_token


def test_get_auth_token_success():
    session = MagicMock()
    session.cookies.get.return_value = "csrf-token"
    response = MagicMock()
    response.json.return_value = {"user": {"auth_token": "abc123"}}
    session.post.return_value = response

    token = get_auth_token("user", "pass", session=session)

    assert token == "abc123"
    session.get.assert_called_once()
    session.post.assert_called_once()


def test_get_auth_token_requires_credentials():
    with pytest.raises(ValueError):
        get_auth_token("", "pass")

    with pytest.raises(ValueError):
        get_auth_token("user", "")


def test_get_auth_token_raises_when_missing_token():
    session = MagicMock()
    session.cookies.get.return_value = None
    response = MagicMock()
    response.json.return_value = {"error": "bad credentials"}
    session.post.return_value = response

    with pytest.raises(TradingViewAuthError):
        get_auth_token("user", "pass", session=session)
