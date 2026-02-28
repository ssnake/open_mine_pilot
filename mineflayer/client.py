from typing import Any
from javascript import require
from threading import Timer
from .tools import Tools
from .events import Events
from agents.base_agent import BaseAgent
import time
mineflayer = require('mineflayer')
# run `uv run python3 -m javascript --install canvas` to install canvas
prismarineViewer   = require("prismarine-viewer")
mineflayerViewer = prismarineViewer.mineflayer

class Client:
    STATE_IDLE = 'idle'
    STATE_CONNECTING = 'connecting'
    STATE_CONNECTED = 'connected'
    STATE_DISCONNECTED = 'disconnected'
    
    def __init__(self, host: str, port: int, username: str):
        
        self._state = self.STATE_IDLE
        self._username = username
        self._bot = mineflayer.createBot({ 
          'host': host, 
          'port': port, 
          'username': username, 
          'hideErrors': False 
        })

        self._viewer = None
            
        self._set_state(self.STATE_CONNECTING)
        self._init_connect_timer()
        self._tools = Tools(self._bot)
        self._events = Events(self, self._bot)
        self._events.bind()
        self._agent = BaseAgent(self)
    
        
    def run(self):
        try:
            self._log('run')
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self._log('KeyboardInterrupt')
            self._set_state(self.STATE_DISCONNECTED)
        pass

    @property
    def tools(self):
        return self._tools
    @property
    def agent(self):
        return self._agent
    @property
    def state(self) -> str:
        return self._state

    def _set_state(self, new_state: str):
        if new_state not in (
            self.STATE_IDLE,
            self.STATE_CONNECTING,
            self.STATE_CONNECTED,
            self.STATE_DISCONNECTED,
        ):
            raise ValueError(f'invalid transport state: {new_state}')
        if self._state != new_state:
            self._log(f'state changed: {self._state} -> {new_state}')
        self._state = new_state

    def _init_connect_timer(self):
        self._reset_connect_timer()

        def _timeout():
            self.on_unable_to_connect('spawn event not received within 5 seconds')

        self._connect_timeout = Timer(5.0, _timeout)
        self._connect_timeout.start()

    def _reset_connect_timer(self):
        if hasattr(self, '_connect_timeout') and self._connect_timeout is not None:
            self._connect_timeout.cancel()
            self._connect_timeout = None

    def on_unable_to_connect(self, reason: str):
        self._log(f'Unable to connect: {reason}')
        self._set_state(self.STATE_DISCONNECTED)    
    
    def _log(self, message: str):
        print(f'{self._username}: {message}')

    def _reassure_viewer(self):
        if self._viewer is None:
            self._viewer = mineflayerViewer(self._bot, {
                'port': 3001,
                'firstPerson': False,
                'viewDistance': 6
            })
            self._log('viewer is initialized')
