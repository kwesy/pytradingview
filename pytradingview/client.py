
import threading
import time
from .chart import ChartSession
from . import protocol
import websocket
from .quote import QuoteSession





class Client():
    
    def __init__(self):
        self.__logged = False
        self.__is_opened = False
        self.__sendQueue = []
        self.sessions = {}

        self.client_bridge = {
            'sessions': self.sessions,
            'send': lambda t, p: self.send(t, p),
            }

        # self.session = {
        #     'Quote': QuoteSession(self.client_bridge),
        #     'Chart': ChartSession(self.client_bridge),
        #     }

        self.Quote = QuoteSession(self.client_bridge)
        self.Chart = ChartSession(self.client_bridge)

        self.__sendQueue.insert(0, protocol.formatWSPacket({'m':'set_auth_token', 'p':['unauthorized_user_token']}))

    def send_queue(self):
        return self.__sendQueue

    @property
    def get_client_brigde(self):
        return self.client_bridge

    @property
    def session(self):
        return self.session

    callbacks = {
    'connected': [],
    'disconnected': [],
    'logged': [],
    'ping': [],
    'data': [],

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
            print('\033[31 ERROR:\033[0m', args)
        else:
            self.handleEvent('error', args)

    
    def on_connected(self, cb):
        self.callbacks['connected'].append(cb)

    def on_disconnected(self, cb):
        self.callbacks['disconnected'].append(cb)

    def on_logged(self, cb):
        self.callbacks['logged'].append(cb)

    def on_ping(self, cb):
        self.callbacks['ping'].append(cb)

    def on_data(self, cb):
        self.callbacks['data'].append(cb)

    def on_error(self, cb):
        self.callbacks['error'].append(cb)

    def on_event(self, cb):
        self.callbacks['event'].append(cb)


    def is_logged(self):
        return self.__logged

    def is_open(self):
        return self.__is_opened

    def send(self,t, p=[]):
        # print('send')
        if not p:
            self.__sendQueue.append(protocol.formatWSPacket(t))
        else:
            self.__sendQueue.append(protocol.formatWSPacket({'m': t, 'p':p}))
        self.sendQueue()

    def sendQueue(self):
        # print(self.__is_opened, self.__logged , len(self.__sendQueue)>0)
        while (self.__is_opened and self.__logged and len(self.__sendQueue)>0):
            packet = self.__sendQueue.pop(0)
            self.wsapp.send(packet)
            # print('\033[;32m-> to server \033[;0m', packet)

    def parsePacket(self, str):
        if not self.is_open: return None 
        
        packets = protocol.parseWSPacket(str)
        # print('here')
        for packet in packets:
            # print(packet)

            try:
                packet = int(packet)
            except:
                pass

            if isinstance(packet, int): # Ping
                # self.send(protocol.formatWSPacket(f'~h~{packet}'),None)
                self.send(f'~h~{packet}')
                self.handleEvent('ping', packet)
                continue
                
            if packet.get('m') == 'protocol_error': # Error
                self.handleError('Client critical error:', packet['p'])
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
                self.handleEvent('logged', packet)
                continue


            self.handleEvent('data',packet)

        # print('after for')
        



    def on_message(self, wsapp, message):
        # print('\033[;34m<- from server \033[;0m', message)
        self.parsePacket(message)
        if not self.__logged and self.__is_opened:
            
            # self.sendQueue()
            self.__logged = True

    def on_error(self, ws, error):
        print('ws error', error, ws)
        pass

    def on_close(self, ws, close_status_code, close_msg):
        self.__logged = False
        self.__is_opened = False
        self.handleEvent('disconnected')
        # print(close_msg)


    def on_open(self, ws):
        self.__is_opened = True
        # print('opened')
        self.handleEvent('connected')
        # self.sendQueue()


    def create_connection(self, options = {}):
        self.wsapp = websocket.WebSocketApp("wss://data.tradingview.com/socket.io/websocket", on_message=self.on_message, on_close=self.on_close, on_open=self.on_open, on_error=self.on_error)
        # self.__sendQueue.insert(0, protocol.formatWSPacket({'m':'set_auth_token', 'p':['unauthorized_user_token']}))
        # self.__logged = True
        # wst = threading.Thread(target=self.wsapp.run_forever, kwargs={'origin':'https://s.tradingview.com'})
        # wst.daemon = True
        # wst.start()
        # time.sleep(2)
        # self.sendQueue()
        self.wsapp.run_forever(origin='https://s.tradingview.com')
        # print('after con')
        

    def end(self, callback):
        self.wsapp.close()
        callback()











