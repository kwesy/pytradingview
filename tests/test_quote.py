from unittest.mock import MagicMock

import pytest

from pytradingview.quote import QuoteSession


@pytest.fixture
def client_bridge():
    return {
        "sessions": {},
        "send": MagicMock(),
        "end": MagicMock(),
    }


@pytest.fixture
def quote_session(client_bridge):
    q = QuoteSession(client_bridge)
    q.set_up_quote({"fields": "price"})
    return q


def test_add_symbols_subscribes_and_fast_tracks(quote_session, client_bridge):
    quote_session.add_symbols(["CME_MINI:ES1!", "CME_MINI:NQ1!"])

    calls = client_bridge["send"].call_args_list
    assert any(call.args[0] == "quote_add_symbols" for call in calls)
    assert any(call.args[0] == "quote_fast_symbols" for call in calls)


def test_on_symbol_and_qsd_dispatch(quote_session):
    received = []
    quote_session.on_symbol("CME_MINI:ES1!", lambda packet: received.append(packet["type"]))

    quote_session.on_data_q(
        {
            "type": "qsd",
            "data": [
                quote_session.session_id,
                {"n": "CME_MINI:ES1!", "v": {"lp": 7000.25}},
            ],
        }
    )

    assert received == ["qsd"]


def test_remove_symbol_unsubscribes(quote_session, client_bridge):
    quote_session.on_symbol("CME_MINI:ES1!", lambda packet: None)
    quote_session.remove_symbol("CME_MINI:ES1!")

    client_bridge["send"].assert_any_call(
        "quote_remove_symbols", [quote_session.session_id, "CME_MINI:ES1!"]
    )
