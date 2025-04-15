# This is just an example code to show how to use this python tradingview client.

from pytradingview.client import Client
# import winsound
# import termcolor


makert = {
  '1':'FX:EURUSD',
  '2':'FOREXCOM:XAUUSD',
  '3':'FX:GBPUSD',
  '4':'FX:USDJPY',
  '5':'BINANCE:BTCUSD',
  '6':'FX:AUDUSD'
}

timeframe = {
  '1':'1',
  '2':'3',
  '3':'5',
  '4':'15',
  '5':'30',
  '6':'45',
  '7':'60',
  '8':'120',
  '9':'240',
  '10':'D'
}

m = input(
  """choose makert type:
  1: EURUSD
  2: XAUUSD
  3: GBPUSD
  4: USDJPY
  5: BTCUSD
  6: AUDUSD
  -:"""
)
while not makert.get(m):
  m = input(
  """
  Invalid index, choose again:  
  """
  )

_m = makert.get(m)

t = input(
  """choose timeframe:
  1: 1min
  2: 3min
  3: 5min
  4: 15min
  5: 30min
  6: 45min
  7: 1h
  8: 2h
  9: 4h
  10: 1D
  -:"""
)
while not timeframe.get(t):
  t = input(
  """
  Invalid index, choose again:  
  """
  )
_t = timeframe.get(t)

watch_price = input('Price to Watch:')
while 1:
  try:
    watch_price = float(watch_price)
    break
  except:
    pass
  watch_price = input('Enter a valid price:')
  

clt = Client()

chart = clt.Chart
chart.set_up_chart()

chart.set_market(_m, { # Set the market
  'timeframe': _t,
  'currency': 'USD',
})

# chart.set_series('240')

handle_err = lambda e: print('Chart error:', e)
chart.on_error( handle_err)

handle_disconnected = lambda e: print('disconnected:', e)
chart.on_error( handle_disconnected)

handle_on_synbol_loaded = lambda e: print(f'''Market "{ chart.get_infos['description'] }" loaded !''')
chart.on_symbol_loaded( handle_on_synbol_loaded)

def handle_update(d):
  sound_alarm = False
  if (not chart.get_periods): return
  if watch_price < 0:
    if float(chart.get_periods['close']) < abs(watch_price):
      sound_alarm = True
  else:
    if float(chart.get_periods['close']) > abs(watch_price):
      sound_alarm = True
    
  if sound_alarm:
    # winsound.Beep(440, 1000)
    print('Target Hit!')
    sound_alarm = False

  # print(termcolor.colored(f''' [{chart.get_infos['description']}]: {chart.get_periods['open']} - {chart.get_periods['close']} {chart.get_infos['currency_id']}''', 'cyan'))
  # print(f''' [{chart.get_infos['description']}]: {chart.get_periods['open']} - {chart.get_periods['close']} {chart.get_infos['currency_id']}''')

chart.on_update(handle_update)

clt.create_connection()
