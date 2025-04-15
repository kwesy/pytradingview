import json
from utils import genSessionID
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

    def __init__(self, client_bridge):
        self.__chart_session_id = genSessionID('cs')
        self.__replay_session_id = genSessionID('rs')
        self.__replay_mode = False
        self.__periods = {}
        self.__current_period = {}
        self.__infos = {}

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
        # print(self.__infos)
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
        # print('self.__infos', packet['type'])

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

        if packet['type'] in ['timescale_update', 'du']:
            changes = []

            keys = packet['data'][1].keys()
            # print(packet['data'])
            for k in keys:
                changes.append(k)
                if k == '$prices':
                    periods = packet['data'][1]['$prices']
                    if not periods or not periods['s']: return

                    for p in periods['s']:
                        self.chart_session['indexes'][p['i']] = p['v']
                        self.__periods[p['v'][0]] = {
                            'time': p['v'][0],
                            'open': p['v'][1],
                            'close': p['v'][4],
                            'max': p['v'][2],
                            'min': p['v'][3],
                            'volume': round(p['v'][5] * 100) / 100,
                        }

                        self.__current_period = {
                            'time': p['v'][0],
                            'open': p['v'][1],
                            'close': p['v'][4],
                            'max': p['v'][2],
                            'min': p['v'][3],
                            'volume': round(p['v'][5] * 100) / 100,
                        }
                        # print('>>>',self.__current_period)

                    continue
                # print('statd1')
                if (self.study_listeners[k]): self.study_listeners[k](packet)
                # print('statd2')

            self.handleEvent('update', changes)
            return

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
        # print('hhhh')
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
        # print(self.series_created)
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

    def fetchMore(self, number = 1):
        self.__client['send']('request_more_data', [self.__chart_session_id, '$prices', number])



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

    # Study = studyructor(self.chartSession)

    def delete(self):
        if (self.__replay_mode): self.__client['send']('replay_delete_session', [self.__replay_session_id])
        self.__client['send']('chart_delete_session', [self.__chart_session_id])
        del self.__client['sessions'][self.__chart_session_id]
        self.__replay_mode = False

