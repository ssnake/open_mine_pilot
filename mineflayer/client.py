from javascript import require
from threading import Timer
from .tools import Tools
from .events import Events
from .action_processor import ActionProcessor
from agents.multi_agent import MultiAgent
import asyncio
mineflayer = require('mineflayer')
# run `uv run python3 -m javascript --install canvas` to install canvas
prismarineViewer   = require("prismarine-viewer")
mineflayerViewer = prismarineViewer.mineflayer

class Client:
    STATE_IDLE = 'idle'
    STATE_CONNECTING = 'connecting'
    STATE_CONNECTED = 'connected'
    STATE_DISCONNECTED = 'disconnected'
    
    def __init__(self, host: str, port: int, username: str, master_username: str, use_say_for_chat: bool = False):
        self._state = self.STATE_IDLE
        self._username = username
        self._master_username = master_username
        self.use_say_for_chat = use_say_for_chat
        self.action_processor = ActionProcessor(self)
        self._bot = mineflayer.createBot({ 
          'host': host, 
          'port': port, 
          'username': username, 
          'hideErrors': False 
        })

        self._viewer = None
            
        self._set_state(self.STATE_CONNECTING)
        self._init_connect_timer()
        self._tools = Tools(self)
        self._agent = MultiAgent(self)
        self._events = Events(self)
        self._events.bind()
    
    async def run(self):
        self._log('run')
        while True:
            try:
                await self.action_processor.process_next()
            except KeyboardInterrupt:
                self._log('KeyboardInterrupt')
                self._set_state(self.STATE_DISCONNECTED)
                break

    @property
    def tools(self):
        return self._tools
    @property
    def agent(self):
        return self._agent

    @property
    def bot(self):
        return self._bot

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
        print(f'[Client]: {message}')

    def _reassure_viewer(self):
        if self._viewer is None:
            self._viewer = mineflayerViewer(self._bot, {
                'port': 3001,
                'firstPerson': False,
                'viewDistance': 6
            })
            self._log('viewer is initialized')
