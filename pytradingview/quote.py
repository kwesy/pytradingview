
from utils import genSessionID




def getQuoteFields(fieldsType):
  if (fieldsType == 'price'):
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
        if (packet['type'] == 'quote_completed'):
          symbol = packet['data'][1]
          if (not self.__symbol_listeners[symbol]):
            self.__client['send']('quote_remove_symbols', [self.__session_id, symbol])
            return
          
          for h in self.__symbol_listeners[symbol]:
            h(packet)
        

        if (packet['type'] == 'qsd'):
          symbol = packet['data'][1]['n']
          if (not self.__symbol_listeners[symbol]):
            self.__client['send']('quote_remove_symbols', [self.__session_id, symbol])
            return
          
          for h in self.__symbol_listeners[symbol]:
            h(packet)

    
    def set_up_quote(self, options:dict = {}):
        self.__client['sessions'][self.__session_id] = {'type':'quote', 'onData':self.on_data_q}

        fields = (options.get('customFields') if options.get('customFields') and (len(options.get('customFields')) > 0)
        else
        getQuoteFields(options.get('fields'))
        )

        self.__client['send']('quote_create_session', [self.__session_id])
        self.__client['send']('quote_set_fields', [self.__session_id]+[fields])

        quoteSession = {
            'sessionID': self.__session_id,
            'symbolListeners': self.__symbol_listeners,
            'send': lambda t, p: self.__client['send'](t, p),
        } 

    def delete(self):
        self.__client['send']('quote_delete_session', [self.__session_id])
        del self.__client['sessions'][self.__session_id]


    