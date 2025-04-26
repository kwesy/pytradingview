import threading
import time
import websocket
from .quote import QuoteSession
from .chart import ChartSession
from . import protocol

class Client():
    """
    A WebSocket client for interacting with TradingView's data stream.
    
    This client manages quote and chart sessions, handles WebSocket communication,
    and provides event-based callbacks for real-time data updates.
    """

    def __init__(self):
        """
        Initializes the Client object, setting up the WebSocket connection parameters,
        session management, and the initial authentication token.
        """
        self.wsapp = None
        self.__logged = False
        self.__is_opened = False
        self.__send_queue = []
        self.sessions = {}

        self.client_bridge = {
            'sessions': self.sessions,
            'send': self.send,
            'end': self.end,
        }

        self.quote = QuoteSession(self.client_bridge)
        self.chart = ChartSession(self.client_bridge)

        self.__send_queue.insert(0, protocol.format_ws_packet({
            'm': 'set_auth_token', 'p': ['unauthorized_user_token']
            })
        )

    @property
    def get_client_brigde(self):
        """
        Property for accessing the client bridge dictionary.

        Returns:
            dict: Dictionary containing client session and send function.
        """
        return self.client_bridge

    @property
    def session(self):
        """
        Property for accessing the active session dictionary.

        Returns:
            dict: Dictionary of active sessions.
        """
        return self.sessions

    callbacks = {
        'connected': [],
        'disconnected': [],
        'logged': [],
        'ping': [],
        'data': [],
        'event': [],
        'error': [],
    }

    def handle_event(self, event, *args):
        """
        Triggers all callbacks registered to a specific event.

        Args:
            event (str): The name of the event.
            *args: Arguments to pass to the callback functions.
        """
        for fun in self.callbacks[event]:
            fun(args)
        for fun in self.callbacks['event']:
            fun(event, args)

    def handle_error(self, *args):
        """
        Handles an error by printing it or triggering the registered error callbacks.

        Args:
            *args: Error information to log or send to callbacks.
        """
        if len(self.callbacks['error']) == 0:
            print('\033[31mERROR:\033[0m', args)
        else:
            self.handle_event('error', args)

    def on_connected(self, cb):
        """Registers a callback for the 'connected' event."""
        self.callbacks['connected'].append(cb)

    def on_disconnected(self, cb):
        """Registers a callback for the 'disconnected' event."""
        self.callbacks['disconnected'].append(cb)

    def on_logged(self, cb):
        """Registers a callback for the 'logged' event."""
        self.callbacks['logged'].append(cb)

    def on_ping(self, cb):
        """Registers a callback for the 'ping' event."""
        self.callbacks['ping'].append(cb)

    def on_data(self, cb):
        """Registers a callback for the 'data' event."""
        self.callbacks['data'].append(cb)

    def on_error(self, cb):
        """Registers a callback for the 'error' event."""
        self.callbacks['error'].append(cb)

    def on_event(self, cb):
        """Registers a callback for all events."""
        self.callbacks['event'].append(cb)

    def is_logged(self):
        """
        Checks if the client is currently authenticated.

        Returns:
            bool: True if logged in, False otherwise.
        """
        return self.__logged

    def is_open(self):
        """
        Checks if the WebSocket connection is currently open.

        Returns:
            bool: True if open, False otherwise.
        """
        return self.__is_opened

    def send(self, t, p=None):
        """
        Sends a packet to the WebSocket, or queues it if the connection is not ready.

        Args:
            t (str or dict): The message type or the full packet dictionary.
            p (list, optional): The payload associated with the message type.
        """
        if p is None:
            p = []
        if not p:
            self.__send_queue.append(protocol.format_ws_packet(t))
        else:
            self.__send_queue.append(protocol.format_ws_packet({'m': t, 'p': p}))
        self.send_queue()

    def send_queue(self):
        """
        Sends all packets in the send queue if the client is logged in and the WebSocket is open.
        """
        while self.__is_opened and self.__logged and len(self.__send_queue) > 0:
            packet = self.__send_queue.pop(0)
            self.wsapp.send(packet)

    def parse_packet(self, string):
        """
        Parses a WebSocket packet string and processes it based on its type.
        Args:
            string (str): The WebSocket packet string to parse.
        Returns:
            None
        Behavior:
            - If the WebSocket connection is not open (self.is_open is False), the method returns None.
            - Parses the input string into individual packets using the protocol.parse_ws_packet function.
            - Iterates through each parsed packet and processes it based on its type:
                - If the packet is an integer, it is treated as a ping message:
                    - Sends a formatted ping response using self.send.
                    - Triggers the ping event with the packet value.
                - If the packet contains a "protocol_error" message (m), it:
                    - Handles the error using self.handle_error.
                    - Closes the WebSocket connection.
                - If the packet contains both a message type (m) and payload (p), it:
                    - Constructs a parsed dictionary with type and data.
                - Checks if the session exists in self.sessions and calls the session's onData handler.
                - If the client is not logged in (self.__logged is False), it triggers the logged event.
                - For all other cases, it triggers the data event with the packet.
        Notes:
            - This method relies on external functions and attributes such as protocol.parse_ws_packet, 
              self.send, self.handle_event, self.handle_error, and self.sessions.
            - Debugging print statements are commented out in the code.
        """
        if not self.is_open:
            return None

        packets = protocol.parse_ws_packet(string)
        for packet in packets:
            try:
                packet = int(packet)
            except (ValueError, TypeError):
                pass

            if isinstance(packet, int): # Ping
                self.send(f'~h~{packet}')
                self.handle_event('ping', packet)
                continue

            if packet.get('m') == 'protocol_error': # Error
                self.handle_error('Client critical error:', packet['p'])
                self.wsapp.close()
                continue

            if packet.get('m') and packet.get('p'): # Normal packet
                parsed = {
                    'type':packet['m'],
                    'data':packet['p']
                }

                session = packet['p'][0]

                if session and self.sessions[session]:
                    self.sessions[session]['onData'](parsed)
                    # print('passed ', parsed)
                    continue

            if not self.__logged:
                self.handle_event('logged', packet)
                continue

            self.handle_event('data',packet)

    def on_message(self, _, message):
        """
        Callback triggered when a WebSocket message is received.

        Args:
            _ (Any): Placeholder for the WebSocketApp instance.
            message (str): The message received.
        """
        self.parse_packet(message)
        if not self.__logged and self.__is_opened:
            self.__logged = True

    def on_close(self, ws, close_status_code, close_msg):
        """
        Callback triggered when the WebSocket connection is closed.

        Args:
            ws (WebSocketApp): The WebSocketApp instance.
            close_status_code (int): The status code for the close.
            close_msg (str): The reason message for the close.
        """
        self.__logged = False
        self.__is_opened = False
        self.handle_event('disconnected', ws, close_status_code, close_msg)

    def on_open(self, ws):
        """
        Callback triggered when the WebSocket connection is opened.

        Args:
            ws (WebSocketApp): The WebSocketApp instance.
        """
        self.__is_opened = True
        self.handle_event('connected', ws)

    def create_connection(self):
        """
        Establishes the WebSocket connection to TradingView and starts listening for messages.
        """
        self.wsapp = websocket.WebSocketApp(
            "wss://data.tradingview.com/socket.io/websocket",
            on_message=self.on_message,
            on_close=self.on_close,
            on_open=self.on_open,
            on_error=self.on_error
        )
        self.wsapp.run_forever(origin='https://s.tradingview.com')

    def end(self, callback):
        """
        Closes the WebSocket connection and executes the provided callback function.

        Args:
            callback (function): A function to be called after the WebSocket connection is closed.
        """
        self.wsapp.close()
        callback()
