import pytest
from unittest.mock import MagicMock, patch

from pytradingview.client import Client


@pytest.fixture
def client():
    c = Client()
    c.wsapp = MagicMock()
    return c


def test_is_logged(client):
    assert client.is_logged() is False
    client._Client__logged = True
    assert client.is_logged() is True


def test_is_open(client):
    assert client.is_open() is False
    client._Client__is_opened = True
    assert client.is_open() is True


def test_send(client):
    with patch("pytradingview.protocol.format_ws_packet") as mock_format:
        mock_format.return_value = "formatted_packet"
        client.send("test_type", ["param1", "param2"])
        assert "formatted_packet" in client._Client__send_queue


def test_set_auth_token(client):
    with patch("pytradingview.protocol.format_ws_packet") as mock_format:
        mock_format.return_value = "auth_packet"
        client.set_auth_token("token-123")
        assert client.auth_token == "token-123"
        assert "auth_packet" in client._Client__send_queue


def test_login_sets_token(client):
    with patch("pytradingview.client.get_auth_token", return_value="auth-token"):
        token = client.login("user", "pass")
        assert token == "auth-token"
        assert client.auth_token == "auth-token"


def test_send_queue(client):
    client._Client__is_opened = True
    client._Client__logged = True
    client._Client__send_queue = ["packet1", "packet2"]

    client.send_queue()

    client.wsapp.send.assert_any_call("packet1")
    client.wsapp.send.assert_any_call("packet2")


def test_parse_packet_ping(client):
    client._Client__is_opened = True

    with patch("pytradingview.protocol.parse_ws_packet", return_value=[123]):
        with patch.object(client, "send") as mock_send:
            with patch.object(client, "handle_event") as mock_event:
                client.parse_packet("ping_packet")

                mock_send.assert_called_once_with("~h~123")
                mock_event.assert_called_once_with("ping", 123)


def test_parse_packet_error(client):
    client._Client__is_opened = True
    with patch("pytradingview.protocol.parse_ws_packet") as mock_parse:
        mock_parse.return_value = [{"m": "protocol_error", "p": ["error_details"]}]
        with patch.object(client, "handle_error") as mock_handle_error:
            client.parse_packet("error_packet")
            mock_handle_error.assert_called_with(
                "Client critical error:", ["error_details"]
            )


def test_on_message(client):
    client._Client__is_opened = True
    with patch.object(client, "parse_packet") as mock_parse:
        with patch.object(client, "send_queue") as mock_send_queue:
            client.on_message(None, "test_message")
            mock_parse.assert_called_with("test_message")
            mock_send_queue.assert_called_once()


def test_init_with_credentials_requests_token():
    with patch("pytradingview.client.get_auth_token", return_value="live-token"):
        client = Client(username="user", password="pass")
        assert client.auth_token == "live-token"


def test_init_with_partial_credentials_fails():
    with pytest.raises(ValueError):
        Client(username="user")

    with pytest.raises(ValueError):
        Client(password="pass")


def test_on_message_no_send_queue_when_closed(client):
    with patch.object(client, "parse_packet") as mock_parse:
        with patch.object(client, "send_queue") as mock_send_queue:
            client.on_message(None, "test_message")
            mock_parse.assert_called_with("test_message")
            mock_send_queue.assert_not_called()


def test_on_close(client):
    client.on_close(None, 1000, "Normal Closure")
    assert client.is_logged() is False
    assert client.is_open() is False


def test_on_open(client):
    client.on_open(None)
    assert client.is_open() is True


def test_create_connection(client):
    with patch("pytradingview.client.websocket.WebSocketApp") as mock_wsapp:
        mock_instance = MagicMock()
        mock_wsapp.return_value = mock_instance

        client.create_connection()

        mock_wsapp.assert_called_with(
            "wss://data.tradingview.com/socket.io/websocket",
            on_message=client.on_message,
            on_close=client.on_close,
            on_open=client.on_open,
            on_error=client.on_ws_error,
        )
        mock_instance.run_forever.assert_called_once()


def test_end(client):
    mock_callback = MagicMock()
    client.end(mock_callback)

    client.wsapp.close.assert_called_once()
    mock_callback.assert_called_once()
