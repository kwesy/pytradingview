"""
TradingView WebSocket Protocol Utilities
========================================

This module provides utility functions for encoding, decoding, compressing, and
parsing WebSocket messages used by TradingView's real-time data feed.

Functions included:
- `parse_ws_packet`: Parses a raw WebSocket message into JSON objects.
- `format_ws_packet`: Encodes a packet (as a dict or string) into the TradingView-specific WebSocket message format.
- `parse_compressed`: Decodes and decompresses a base64-encoded, zlib-compressed JSON string.

Constants:
- `CLEANER_RGX`: Regex pattern to remove heartbeat tokens.
- `SPLITTER_RGX`: Regex pattern to split raw WebSocket messages into individual packets.

These functions are essential for interpreting and composing the custom protocol used
by TradingView's socket.io-based WebSocket API.
"""

import re
import json
import zlib
import base64


CLEANER_RGX = '~h~'
SPLITTER_RGX = '~m~[0-9]{1,}~m~'

def parse_ws_packet(string):
    """
    Parses a WebSocket packet string into a list of JSON objects.

    This function takes a string input, cleans it using a regular expression,
    splits it into parts based on another regular expression, and attempts to
    parse each part as a JSON object. Successfully parsed JSON objects are
    appended to a list, which is then returned. If a part cannot be parsed,
    a warning message is printed to the console.

    Args:
        string (str): The WebSocket packet string to be parsed.

    Returns:
        list: A list of JSON objects parsed from the input string.

    Notes:
        - The function uses `cleanerRgx` to clean the input string.
        - The function uses `splitterRgx` to split the cleaned string into parts.
        - If a part cannot be parsed as JSON, it is skipped, and a warning is printed.
    """
    l = re.split(SPLITTER_RGX, re.sub(CLEANER_RGX, '', string))
    packet = []
    for p in l:
        if not p:
            continue
        try:
            packet.append(json.loads(p))
        except json.JSONDecodeError:
            pass
    return packet

def format_ws_packet(packet):
    """
    Formats a WebSocket packet to the required TradingView format.

    This function converts a dictionary packet into a compact JSON string,
    replacing any `null` values with empty strings, and prepends the message 
    with a length header in the format `~m~<length>~m~`.

    Args:
        packet (dict or str): The packet to format. If it's a dictionary, 
                              it will be converted to a JSON string.

    Returns:
        str: The formatted WebSocket packet as a string.
    """
    if isinstance(packet, dict):
        packet = json.dumps(packet, separators=(',', ':')).replace('null', '""')
    return f'~m~{len(packet)}~m~{packet}'

def parse_compressed(data):
    """
    Decompresses and decodes a base64-encoded, zlib-compressed JSON string.

    This function is used to handle compressed WebSocket data received 
    from the server, typically for efficiency in data transmission.

    Args:
        data (str): The compressed and base64-encoded string.

    Returns:
        object: The decompressed and parsed JSON content as a Python object 
                (typically a dict or list).
    """
    return json.load(zlib.decompress(base64.b64decode(data)))
