"""
Quote Session Management for TradingView WebSocket API
======================================================

This module provides tools for managing quote sessions using TradingView's
WebSocket-based real-time data API. It includes session creation, data
handling, and field configuration for streaming quote updates.

Main Components:
----------------

- **getQuoteFields(fieldsType)**:
    Utility function to retrieve the appropriate list of fields based on the requested detail level.

- **QuoteSession**:
    A class representing a single quote session. It manages symbol subscriptions,
    incoming data handling, and session lifecycle with methods like `set_up_quote` and `delete`.

Key Features:
-------------
- Flexible field selection via custom fields or predefined groups.
- Symbol-level listener registration for quote updates.
- Automatic cleanup of unsubscribed symbols.
- Session management through a client bridge interface.

Dependencies:
-------------
- `genSessionID` from the `.utils` module for generating unique session identifiers.

Intended Usage:
---------------
This module is designed to be used as part of a WebSocket client system interfacing
with TradingView's data feed. The `QuoteSession` class should be instantiated and controlled
by a higher-level client class which handles the WebSocket connection.

Example:
--------
```python
quote_session = QuoteSession(client_bridge)
quote_session.set_up_quote({'fields': 'price'})
"""

from .utils import genSessionID


def get_quote_fields(fields_type:str):
    """
    Returns a list of quote fields based on the specified field type.

    This function determines which fields to request from the quote session
    depending on the level of detail required.

    Args:
        fieldsType (str): The type of fields to retrieve. Supported value:
            - 'price': Returns a minimal set of fields focused on last price (`'lp'`).

    Returns:
        list: A list of field names (strings) to include in quote updates.

    Notes:
        - If `fieldsType` is not `'price'`, a comprehensive list of fields is returned,
          which includes metadata, financials, and real-time trading data.
    """

    if fields_type == 'price':
        return ['lp']

    return [
      'base-currency-logoid', 'ch', 'chp', 'currency-logoid',
      'currency_code', 'current_session', 'description',
      'exchange', 'format', 'fractional', 'is_tradable',
      'language', 'local_description', 'logoid', 'lp',
      'lp_time', 'minmov', 'minmove2', 'original_name',
      'pricescale', 'pro_name', 'short_name', 'type',
      'update_mode', 'volume', 'ask', 'bid', 'fundamentals',
      'high_price', 'low_price', 'open_price', 'prev_close_price',
      'rch', 'rchp', 'rtc', 'rtc_time', 'status', 'industry',
      'basic_eps_net_income', 'beta_1_year', 'market_cap_basic',
      'earnings_per_share_basic_ttm', 'price_earnings_ttm',
      'sector', 'dividends_yield', 'timezone', 'country_code',
      'provider_id',
    ]


class QuoteSession:

    def __init__(self, client_bridge) -> None:
        self.__session_id = genSessionID('qs')
        self.__client = client_bridge
        self.__symbol_listeners = {}

    def on_data_q(self, packet):
        """
        Handles incoming quote data packets and dispatches them to registered symbol listeners.

        This method processes two types of quote-related messages:
        - `'quote_completed'`: Indicates that the initial quote data for a symbol has been loaded.
        - `'qsd'`: Represents a streaming quote update.

        For both types:
        - Extracts the symbol from the packet.
        - Checks if there are any registered listeners for that symbol.
            - If no listeners exist, it sends a request to remove the symbol from the quote session.
        - If listeners are found, the packet is dispatched to each listener callback.

        Args:
            packet (dict): The incoming WebSocket packet with keys:
                - `type` (str): The type of the message, e.g., `'quote_completed'` or `'qsd'`.
                - `data` (list): The payload, which contains the symbol and associated data.

        Notes:
            - Assumes `self.__symbol_listeners` is a dictionary mapping symbols to lists of callback functions.
            - Assumes `self.__client['send']` is a callable that sends a message to the WebSocket server.
            - Assumes `self.__session_id` identifies the current quote session.
        """

        if packet['type'] == 'quote_completed':

            symbol = packet['data'][1]
            if not self.__symbol_listeners[symbol]:
                self.__client['send']('quote_remove_symbols', [self.__session_id, symbol])
                return

            for h in self.__symbol_listeners[symbol]:
                h(packet)

        if packet['type'] == 'qsd':
            symbol = packet['data'][1]['n']
            if not self.__symbol_listeners[symbol]:
                self.__client['send']('quote_remove_symbols', [self.__session_id, symbol])
                return

            for h in self.__symbol_listeners[symbol]:
                h(packet)

    def set_up_quote(self, options: dict = None):
        """
        Initializes and configures a quote session for receiving real-time market data.

        This method:
        - Registers the current quote session in the client session manager.
        - Sets up fields to be tracked based on user-provided options or default field configuration.
        - Sends messages to the server to create the quote session and define the fields.
        - Prepares a dictionary representing the quote session (e.g., for use by other components).

        Args:
            options (dict, optional): Configuration options for the quote session.
                - 'customFields' (list, optional): A list of field names to use instead of defaults.
                - 'fields' (str, optional): A string indicating a preset or type of field group to use,
                                            passed to `getQuoteFields()` if `customFields` is not used.

        Behavior:
            - If 'customFields' is present and non-empty, it is used directly.
            - Otherwise, it falls back to using `getQuoteFields(fields)` to get the default fields.
            - The quote session is identified by `self.__session_id`.
            - All quote updates are handled by `self.on_data_q`.
        
        Notes:
            - Assumes `self.__client['send']` is a function to send WebSocket messages.
            - Assumes `self.__symbol_listeners` is a dictionary of symbol-specific handlers.
            - Assumes `getQuoteFields()` is a helper function to generate field sets.
            - The method prepares a `quoteSession` dictionary but does not store or return it.
        """

        if options is None:
            options = {}

        self.__client['sessions'][self.__session_id] = {'type':'quote', 'onData':self.on_data_q}

        fields = (options.get('customFields') if options.get('customFields') and
                  (len(options.get('customFields')) > 0)
                  else
                    get_quote_fields(options.get('fields'))
        )

        self.__client['send']('quote_create_session', [self.__session_id])
        self.__client['send']('quote_set_fields', [self.__session_id]+[fields])

        quote_session = {
            'sessionID': self.__session_id,
            'symbolListeners': self.__symbol_listeners,
            # 'send': lambda t, p: self.__client['send'](t, p),
            'send': self.__client['send'],
        }

    def delete(self):
        """
        Deletes the current quote session from the client.

        This method performs the following:
        - Sends a request to the server to delete the quote session identified by `self.__session_id`.
        - Removes the session entry from the local `self.__client['sessions']` dictionary.

        Notes:
            - Assumes `self.__client['send']` is a valid function to send WebSocket messages.
            - This operation is irreversible for the current session ID once called.
        """

        self.__client['send']('quote_delete_session', [self.__session_id])
        del self.__client['sessions'][self.__session_id]
