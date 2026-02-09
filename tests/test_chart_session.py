import datetime
import json
import pytest
from unittest.mock import MagicMock, patch

from pytradingview.chart import ChartSession


@pytest.fixture
def client_bridge():
    return {
        "sessions": {},
        "send": MagicMock(),
        "end": MagicMock(),
    }


@pytest.fixture
def chart_session(client_bridge): 
    chart = ChartSession(client_bridge)
    chart.set_up_chart()
    return chart


def test_set_timezone(chart_session, client_bridge):
    chart_session.set_timezone("America/New_York")

    client_bridge["send"].assert_called_with(
        "switch_timezone",
        [chart_session.chart_session["sessionID"], "America/New_York"],
    )


def test_set_market(chart_session, client_bridge):
    chart_session.set_market("AAPL", {"adjustment": "splits"})

    # grab the resolve_symbol call
    calls = [
        call for call in client_bridge["send"].call_args_list
        if call.args[0] == "resolve_symbol"
    ]
    assert len(calls) == 1

    _, args = calls[0].args
    session_id, series_id, payload = args

    # series id is dynamic
    assert series_id.startswith("ser_")

    # payload starts with '=' → strip it
    assert payload.startswith("=")
    data = json.loads(payload[1:])

    assert data == {
        "symbol": "AAPL",
        "adjustment": "splits",
    }


def test_set_series(chart_session, client_bridge):
    chart_session.current_series = 1
    chart_session.set_series(timeframe="60", range=50)

    client_bridge["send"].assert_called_with(
        "create_series",
        [
            chart_session.chart_session["sessionID"],
            "$prices",
            "s1",
            "ser_1",
            "60",
            50,
        ],
    )


def test_fetch_more(chart_session, client_bridge):
    chart_session.fetch_more(200)

    client_bridge["send"].assert_called_with(
        "request_more_data",
        [chart_session.chart_session["sessionID"], "$prices", 200],
    )


def test_download_data(chart_session):
    start = datetime.datetime(2023, 1, 1)
    end = datetime.datetime(2023, 1, 10)

    with patch.object(chart_session, "on_series_loaded") as mock_loaded:
        chart_session.download_data(start, end, "test.csv")
        mock_loaded.assert_called_once()


def test_on_event_callbacks(chart_session):
    mock_callback = MagicMock()

    chart_session.on_update(mock_callback)
    chart_session.handleEvent("update", {"key": "value"})

    mock_callback.assert_called_once_with(({"key": "value"},))


