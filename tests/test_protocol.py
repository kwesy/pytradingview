import json
import base64
import zlib

from pytradingview.protocol import (
    parse_ws_packet,
    format_ws_packet,
    parse_compressed,
)


def test_parse_ws_packet():
    raw_message = '~m~7~m~{"a":1}~m~13~m~{"b":2,"c":3}'
    expected = [{"a": 1}, {"b": 2, "c": 3}]
    assert parse_ws_packet(raw_message) == expected

    raw_message_with_heartbeat = "~h~~m~5~m~{\"a\":1}"
    expected = [{"a": 1}]
    assert parse_ws_packet(raw_message_with_heartbeat) == expected

    invalid_message = '~m~7~m~{"a":1}~m~7~m~invalid_json'
    assert parse_ws_packet(invalid_message) == [{"a": 1}]


def test_format_ws_packet():
    packet = {"a": 1, "b": None}
    expected = '~m~14~m~{"a":1,"b":""}'
    assert format_ws_packet(packet) == expected

    packet_str = '{"a":1,"b":""}'
    assert format_ws_packet(packet_str) == expected


def test_parse_compressed():
    original_data = {"key": "value", "list": [1, 2, 3]}
    compressed_data = base64.b64encode(
        zlib.compress(json.dumps(original_data).encode())
    ).decode()

    assert parse_compressed(compressed_data) == original_data
