from typing import Any
from javascript import require, On, Once, AsyncTask, once, off
from threading import Timer
import time
from .tools import Tools


mineflayer = require('mineflayer')
# run `uv run python3 -m javascript --install canvas` to install canvas
prismarineViewer   = require("prismarine-viewer")
mineflayerViewer = prismarineViewer.mineflayer

class Client:
    STATE_IDLE = 'idle'
    STATE_CONNECTING = 'connecting'
    STATE_CONNECTED = 'connected'
    STATE_DISCONNECTED = 'disconnected'
    
    def __init__(self, host: str, port: int, username: str, agent: Any):
        
        self._agent = agent
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
        self._bind_events()
        self._tools = Tools(self._bot)
    
        
    def run(self):
        # try:
        #     self._log('run')
        #     while True:
        #         time.sleep(0.1)
        # except KeyboardInterrupt:
        #     self._log('KeyboardInterrupt')
        #     self._set_state(self.STATE_DISCONNECTED)
        pass
    
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

    def _bind_events(self):
        @On(self._bot, 'chat')
        def _on_chat(this, username, message, *rest):
            self._log(f'Chat: {username}: {message}')
            if username == 'Server':
                @AsyncTask(start=True)
                def start(task):
                    self._tools.handle_message(message)

        @On(self._bot, 'end')
        def _on_end(this, reason, *rest):
            self._log(f'End: {reason}')
            pass
            
        @On(self._bot, 'error')
        def _on_error(this, error, *rest):
            self._log(f'Error: {error}')
            pass

        @On(self._bot, 'spawn')
        def _on_spawn(this):
            self._log(f'Spawn')
            self._reassure_viewer()
            self._set_state(self.STATE_CONNECTED)
            self._reset_connect_timer()
            
            # @AsyncTask(start=True)
            # def start(task):
            #     self._tools.handle_message('go')
            pass

        @On(self._bot, 'login')
        def _on_login(this):
            self._log(f'Login')
            pass

        # keep a reference so the handler is not garbage-collected
        self._on_chat = _on_chat
        self._on_end = _on_end
        self._on_error = _on_error
        self._on_spawn = _on_spawn
        self._on_login = _on_login

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
