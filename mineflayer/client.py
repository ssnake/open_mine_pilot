from javascript import require
from threading import Timer, BrokenBarrierError
from contextlib import suppress
from .tools import Tools
from .events import Events
from .action_processor import ActionProcessor
from agents.multi_agent import MultiAgent
from logger import log
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
        self._events = Events(self)
        self._events.bind()

        self._set_state(self.STATE_CONNECTING)
        self._log(f'connecting to {host}:{port} as {username}')
        self._tools = Tools(self)
        self._agent = MultiAgent(self)
        self._init_connect_timer()
    
    async def run(self):
        self._log('run')
        heartbeat = asyncio.create_task(self._heartbeat_loop())
        try:
            while True:
                try:
                    await self.action_processor.process_next()
                except asyncio.CancelledError:
                    self._log('CancelledError')
                    self._set_state(self.STATE_DISCONNECTED)
                    raise
                if self._state == self.STATE_DISCONNECTED:
                    self._log('disconnected, stopping run loop')
                    break
        finally:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat

    async def _heartbeat_loop(self, interval: float = 1.0, probe_timeout: float = 3.0):
        loop = asyncio.get_running_loop()
        while self._state != self.STATE_DISCONNECTED:
            await asyncio.sleep(interval)
            if self._state != self.STATE_CONNECTED:
                continue
            try:
                await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._bot.entity.position),
                    timeout=probe_timeout,
                )
            except asyncio.TimeoutError:
                self._log('heartbeat: JS bridge unresponsive (asyncio timeout)')
                self._set_state(self.STATE_DISCONNECTED)
                return
            except BrokenBarrierError as e:
                self._log(f'heartbeat: JS bridge thread dead ({e})')
                self._set_state(self.STATE_DISCONNECTED)
                return
            except Exception as e:
                if 'Timed out accessing' in str(e):
                    self._log(f'heartbeat: JS bridge IPC dead ({e})')
                    self._set_state(self.STATE_DISCONNECTED)
                    return
                self._log(f'heartbeat: unexpected probe error: {e}')

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
    
    def _log(self, message: str, trace_id: str | None = None):
        log('Client', message, trace_id)

    def _reassure_viewer(self):
        if self._viewer is None:
            self._viewer = mineflayerViewer(self._bot, {
                'port': 3001,
                'firstPerson': False,
                'viewDistance': 6
            })
            self._log('viewer is initialized, open http://localhost:3001 to view')
