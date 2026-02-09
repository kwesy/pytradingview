from datetime import datetime, timedelta
import pytest

from pytradingview.utils import genSessionID, strip_html_tags, parse_datetime


def test_genSessionID():
    session_id = genSessionID()
    assert session_id.startswith("xs_")
    assert len(session_id) == 15

    session_id_custom = genSessionID(type="custom")
    assert session_id_custom.startswith("custom_")
    assert len(session_id_custom) == 19


def test_strip_html_tags():
    html = "<p>This is <b>bold</b> and <i>italic</i>.</p>"
    expected = "This is bold and italic."
    assert strip_html_tags(html) == expected

    assert strip_html_tags("") == ""


def test_parse_datetime():
    now = datetime.now()

    parsed_now = parse_datetime("now")
    assert abs(parsed_now - now) <= timedelta(seconds=1)

    parsed_plus_1d = parse_datetime("+1d")
    expected_plus_1d = now + timedelta(days=1)
    assert abs(parsed_plus_1d - expected_plus_1d) <= timedelta(seconds=1)

    parsed_minus_1w = parse_datetime("-1w")
    expected_minus_1w = now - timedelta(weeks=1)
    assert abs(parsed_minus_1w - expected_minus_1w) <= timedelta(seconds=1)


