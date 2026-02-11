"""
TradingView authentication helpers.
"""

from typing import Optional

import requests


SIGN_IN_URL = "https://www.tradingview.com/accounts/signin/"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tradingview.com/",
    "Origin": "https://www.tradingview.com",
}


class TradingViewAuthError(RuntimeError):
    """Raised when TradingView login does not return an auth token."""


def get_auth_token(
    username: str,
    password: str,
    timeout: int = 20,
    session: Optional[requests.Session] = None,
) -> str:
    """
    Exchange TradingView username/password credentials for an auth token.
    """
    if not username or not password:
        raise ValueError("username and password are required")

    session_obj = session or requests.Session()

    # Prime CSRF cookies if available; some deployments enforce this.
    try:
        session_obj.get(SIGN_IN_URL, headers=DEFAULT_HEADERS, timeout=timeout)
    except requests.RequestException:
        # Continue to POST attempt; endpoint behavior can vary by region/edge.
        pass

    csrf_token = session_obj.cookies.get("csrftoken")
    payload = {
        "username": username,
        "password": password,
        "remember": "on",
    }

    headers = dict(DEFAULT_HEADERS)
    headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"

    if csrf_token:
        payload["csrfmiddlewaretoken"] = csrf_token
        headers["X-CSRFToken"] = csrf_token

    response = session_obj.post(
        SIGN_IN_URL,
        data=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()

    try:
        data = response.json()
    except ValueError as exc:
        raise TradingViewAuthError("sign-in response was not JSON") from exc

    token = data.get("user", {}).get("auth_token")
    if not token:
        code = data.get("code")
        message = data.get("error") or data.get("message") or "auth token missing"
        if code:
            message = f"{message} (code={code})"
        raise TradingViewAuthError(message)

    return token
