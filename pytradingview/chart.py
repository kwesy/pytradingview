import csv
import datetime
import json
import math
import os
import time

import requests
from .utils import genSessionID, strip_html_tags
from operator import itemgetter


chart_types = {
  'HeikinAshi': 'BarSetHeikenAshi@tv-basicstudies-60!',
  'Renko': 'BarSetRenko@tv-prostudies-40!',
  'LineBreak': 'BarSetPriceBreak@tv-prostudies-34!',
  'Kagi': 'BarSetKagi@tv-prostudies-34!',
  'PointAndFigure': 'BarSetPnF@tv-prostudies-34!',
  'Range': 'BarSetRange@tv-basicstudies-72!',
}


class ChartSession:
    """
    ChartSession is a class that manages chart and replay sessions for interacting with a client bridge. 
    It provides methods to set up charts, handle events, manage market data, and configure replay sessions.
    Attributes:
        chart_session (dict): A dictionary containing session ID, study listeners, indexes, and a send function.
        current_series (int): Tracks the current series index.
        series_created (bool): Indicates whether a series has been created.
        callbacks (dict): A dictionary of event callbacks for handling various events like updates, errors, and replay events.
    Methods:
        get_periods: Returns the current period data.
        get_all_periods: Returns all periods sorted in reverse order.
        get_infos: Returns information about the current symbol.
        handleEvent(event, *args): Executes all callbacks associated with a specific event.
        handleError(*args): Handles errors by either printing them or invoking error callbacks.
        on_data_c(packet): Processes chart-related data packets and updates periods or triggers events.
        on_data_r(packet): Processes replay-related data packets and triggers replay events.
        set_up_chart(): Sets up chart and replay sessions with the client bridge.
        set_timezone(timezone="Etc/UTC"): Sets the timezone for the chart session.
        set_series(timeframe='240', range=100, reference=None): Configures the series for the chart session.
        set_market(symbol, options={}): Sets the market symbol and options for the chart session.
        fetchMore(number=1): Requests more data for the chart session.
        on_symbol_loaded(cb): Registers a callback for the 'symbolLoaded' event.
        on_update(cb): Registers a callback for the 'update' event.
        on_replay_loaded(cb): Registers a callback for the 'replayLoaded' event.
        on_replay_resolution(cb): Registers a callback for the 'replayResolution' event.
        on_replay_end(cb): Registers a callback for the 'replayEnd' event.
        on_replay_point(cb): Registers a callback for the 'replayPoint' event.
        on_error(cb): Registers a callback for the 'error' event.
        delete(): Deletes the chart and replay sessions and cleans up resources.
    """

    def __init__(self, client_bridge):
        self.__chart_session_id = genSessionID('cs')
        self.__replay_session_id = genSessionID('rs')
        self.__replay_mode = False
        self.__periods = {}
        self.__current_period = {}
        self.__infos = {}
        self.collected_data = [] # List to store collected data

        self.__replaya_OKCB = {}
        self.__client = client_bridge

        self.study_listeners = {}

        # ChartSessionBridge
        self.chart_session = {
            'sessionID': self.__chart_session_id,
            'studyListeners': self.study_listeners,
            'indexes': {},
            'send': lambda t, p: self.__client['send'](t, p)
        }

        self.current_series = 0
        self.series_created = False

    @property
    def get_periods(self):
        # return sorted(self.__periods.items(), reverse=True)
        return self.__current_period

    @property
    def get_all_periods(self):
        return sorted(self.__periods.items(), reverse=True)

    @property
    def get_infos(self):
        return self.__infos

    
    callbacks = {
        'seriesLoaded': [],
        'symbolLoaded': [],
        'update': [],

        'replayLoaded': [],
        'replayPoint': [],
        'replayResolution': [],
        'replayEnd': [],

        'event': [],
        'error': [],
    }

    def handleEvent(self,event, *args):
        for fun in self.callbacks[event]:
            fun(args)
        for fun in self.callbacks['event']:
            fun(event, args)

    def handleError(self,*args):
        if len(self.callbacks['error']) == 0:
            print('\033[31m ERROR:\033[0m', args)
        else:
            self.handleEvent('error', args)
    
    def on_data_c(self, packet):
        if isinstance(packet['data'][1], str) and self.study_listeners.get(packet['data'][1]):
            self.study_listeners[packet['data'][1]](packet)
            return

        if packet['type'] == 'symbol_resolved':
            self.__infos = {
            'series_id': packet['data'][1],
            **packet['data'][2]
          }

            self.handleEvent('symbolLoaded')
            return

        if packet['type'] == 'timescale_update': # historical data loaded
            periods = packet['data'][1]['$prices']['s']

            if not periods:
                return
            
            candles = []
            for p in periods:
                c = {
                    'time': p['v'][0],
                    'open': p['v'][1],
                    'close': p['v'][4],
                    'high': p['v'][2],
                    'low': p['v'][3],
                    'volume': round(p['v'][5] * 100) / 100,
                }
                candles.append(c)
            self.handleEvent('seriesLoaded', candles)

        if packet['type'] == 'du': # current candle update
            changes = []

            keys = packet['data'][1].keys()

            for k in keys:
                changes.append(k)
                if k == '$prices':
                    periods = packet['data'][1]['$prices']['s']

                    if not periods:
                        return

                    for p in periods:
                        self.chart_session['indexes'][p['i']] = p['v']
                        self.__periods[p['v'][0]] = {
                            'time': p['v'][0],
                            'open': p['v'][1],
                            'close': p['v'][4],
                            'high': p['v'][2],
                            'low': p['v'][3],
                            'volume': round(p['v'][5] * 100) / 100,
                        }

                        self.__current_period = {
                            'time': p['v'][0],
                            'open': p['v'][1],
                            'close': p['v'][4],
                            'high': p['v'][2],
                            'low': p['v'][3],
                            'volume': round(p['v'][5] * 100) / 100,
                        }

                    continue
                if (self.study_listeners[k]): self.study_listeners[k](packet)

            self.handleEvent('update', changes)
            return

        ## Error handling
        if packet['type'] == 'symbol_error':
            self.handleError(f"({packet['data'][1]}) Symbol error:", packet['data'][2])
            return

        if packet['type'] == 'series_error':
            self.handleError('Series error:', packet['data'][3])
            return

        if packet['type'] == 'critical_error':
            _, name, description = packet['data']
            self.handleError('Critical error:', name, description)

    def on_data_r(self, packet):
        if (packet['type'] == 'replay_ok'):
          if (self.__replaya_OKCB[packet['data'][1]]):
            self.__replaya_OKCB[packet['data'][1]]()
            del self.__replaya_OKCB[packet['data'][1]]
          return

        if (packet['type'] == 'replay_instance_id'):
          self.handleEvent('replayLoaded', packet['data'][1])
          return

        if (packet['type'] == 'replay_point'):
          self.handleEvent('replayPoint', packet['data'][1])
          return

        if (packet['type'] == 'replay_resolutions'):
          self.handleEvent('replayResolution', packet['data'][1], packet['data'][2])
          return

        if (packet['type'] == 'replay_data_end'):
          self.handleEvent('replayEnd')
          return

        if (packet['type'] == 'critical_error'):
            _, name, description = packet['data']
            self.handleError('Critical error:', name, description)

    def set_up_chart(self):
        self.__client['sessions'][self.__chart_session_id] = {'type':'chart', 'onData': self.on_data_c}
        self.__client['sessions'][self.__replay_session_id] = {'type':'replay', 'onData': self.on_data_r}
        self.__client['send']('chart_create_session', [self.__chart_session_id])
    
    def set_timezone(self, timezone:str="Etc/UTC"):
        self.__client['send']("switch_timezone",[self.__chart_session_id,timezone])

    def set_series(self, timeframe = '240', range = 100, reference = None):

        if (not self.current_series):
            self.handleError('Please set the market before setting series')
            return

        calcRange = range if not reference else ['bar_count', reference, range]

        self.periods = {}

        self.__client['send'](f"{'modify' if self.series_created else 'create'}_series", [ # create_series or modify_series
        self.__chart_session_id,
        '$prices',
        's1',
        f'ser_{self.current_series}',
        timeframe,
        '' if self.series_created else calcRange,
        ])
        self.series_created = True

    def set_market(self, symbol, options:dict = {}):
        self.periods = {}

        if (self.__replay_mode):
            self.__replay_mode = False
            self.__client['send']('replay_delete_session', [self.__replay_session_id])

        symbolInit = {
        'symbol': symbol or 'BTCEUR',
        'adjustment': options.get('adjustment') or 'splits',
        }

        if options.get('session'): symbolInit['session'] = options.get('session')
        if options.get('currency'): symbolInit['currency-id'] = options.get('currency')

        if options.get('replay'):
            self.__replay_mode = True
            self.__client['send']('replay_create_session', [self.__replay_session_id])

            self.__client['send']('replay_add_series', [
                self.__replay_session_id,
                'req_replay_addseries',
                f'=${json.dumps(symbolInit)}',
                options.get('timeframe'),
            ])

            self.__client['send']('replay_reset', [
                self.__replay_session_id,
                'req_replay_reset',
                options.get('replay'),
            ])
        
        complex = options.get('type') or options.get('replay')
        chartInit = {} if complex else symbolInit

        if (complex):
            if options.get('replay'): chartInit['replay'] = self.__replay_session_id
            chartInit['symbol'] = symbolInit
            chartInit['type'] = chart_types[options.get('type')]
            if options.get('type'): chartInit['inputs'] = { } + options.get('inputs')

        self.current_series += 1

        self.__client['send']('resolve_symbol', [
        self.__chart_session_id,
        f'ser_{self.current_series}',
        f'={json.dumps(chartInit)}',
        ])

        self.set_series(options.get('timeframe'), options.get('range') or 100, options.get('to'))

    def fetch_more(self, number = 100):
        self.__client['send']('request_more_data', [self.__chart_session_id, '$prices', number])

    def save_batch(self, batch:list, filename):
        try:
            file_exists = os.path.isfile(filename)

            with open(filename, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["time", "open", "high", "low", "close", "volume"])

                if not file_exists:
                    writer.writeheader()  # Write header only once

                for row in batch:
                    writer.writerow(row)

            print(f"Saved batch of {len(batch)} candles to {filename}")
        except Exception as e:
            print(f"Error saving batch: {e}")

    def download_data(self, start:datetime.datetime, end:datetime.datetime, filename):
        """
        Downloads historical data for the specified time range and saves it to a CSV file.
        Args:
            start (int): The start time in milliseconds since epoch.
            end (int): The end time in milliseconds since epoch.
            filename (str): The name of the CSV file to save the data.
        """

        batch_size = 100

        self.collected_data = []

        # convert to Unix timestamps (seconds)
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())

        def on_batch_loaded(args):
            # Filter data within range
            data = args[0]
            filtered = [c for c in data if start_ts <= c["time"] <= end_ts]
            self.collected_data.extend(filtered)

            # Check if we've reached or passed the start timestamp
            oldest_ts = min(c["time"] for c in data)
            if oldest_ts <= start_ts:
                sorted_data = sorted(self.collected_data, key=lambda x: x['time'], reverse=True)
                self.save_batch(sorted_data, filename)
                self.__client['end']() # close the connection
                print("✅ Finished downloading requested range.")
                return
             
            self.fetch_more(batch_size)

        self.on_series_loaded(on_batch_loaded)

    def search_symbols(self, query: str, max_results=200, country="US", lang="en") -> list:
        """
        Searches for trading symbols using the TradingView symbol search API.
        Args:
            query (str): The search query string to look for symbols.
            max_results (int, optional): The maximum number of results to return. Defaults to 200.
            country (str, optional): The country code to filter results by. Defaults to "US".
            lang (str, optional): The language code for the search results. Defaults to "en".
        Returns:
            list: A list of dictionaries containing symbol information. Each dictionary includes:
                - "symbol" (str): The formatted symbol string (e.g., "EXCHANGE:SYMBOL").
                - "description" (str): A description of the symbol.
                - "type" (str): The type of the symbol (e.g., "stock", "crypto").
        Raises:
            requests.exceptions.RequestException: If the HTTP request to the API fails.
            ValueError: If the response from the API is invalid or cannot be parsed.
        """

        url = "https://symbol-search.tradingview.com/symbol_search/v3/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.tradingview.com/",
            "Origin": "https://www.tradingview.com",
        }

        results = []
        start = 0

        while len(results) < max_results:
            params = {
                "text": query,
                "hl": 1,
                "exchange": "",
                "lang": lang,
                "search_type": "undefined",
                "domain": "production",
                "sort_by_country": country,
                "promo": "true",
                "start": start
            }

            resp = requests.get(url, params=params, headers=headers, timeout=20)
            resp.raise_for_status()

            data = resp.json()
            chunk = data.get("symbols", [])
            symbols_remaining = data.get("symbols_remaining", 0)

            results.extend(chunk)
            start += len(chunk)

            if not symbols_remaining or not chunk:
                break

        return [{
            "symbol": strip_html_tags(f"{item.get('prefix', item.get('source_id'))}:{item['symbol']}"),
            "description": strip_html_tags(item.get("description", "")),
            "type": item.get("type", "")
        } for item in results[:max_results]]


    def on_series_loaded(self, cb):
        self.callbacks['seriesLoaded'].append(cb)

    def on_symbol_loaded(self, cb):
        self.callbacks['symbolLoaded'].append(cb)

    def on_update(self, cb):
        self.callbacks['update'].append(cb)

    def on_replay_loaded(self, cb):
        self.callbacks['replayLoaded'].append(cb)

    def on_replay_resolution(self, cb):
        self.callbacks['replayResolution'].append(cb)

    def on_replay_end(self, cb):
        self.callbacks['replayEnd'].append(cb)

    def on_replay_point(self, cb):
        self.callbacks['replayPoint'].append(cb)

    def on_error(self, cb):
        self.callbacks['error'].append(cb)

    def delete(self):
        if (self.__replay_mode): self.__client['send']('replay_delete_session', [self.__replay_session_id])
        self.__client['send']('chart_delete_session', [self.__chart_session_id])
        del self.__client['sessions'][self.__chart_session_id]
        self.__replay_mode = False
