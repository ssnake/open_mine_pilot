from open_mine_pilot import Transport
from javascript import require, On, Once, AsyncTask, once, off
from threading import Timer

mineflayer = require('mineflayer')


class MineflayerTransport(Transport):
    def __init__(self, host: str, port: int, username: str):
        super().__init__(username)

        self._bot = mineflayer.createBot({ 
            'host': host, 
            'port': port, 
            'username': username, 
            'hideErrors': False 
        })

        self._init_connect_timer()
        self._bind_events()
    
    def say(self, message: str):
        self._bot.chat(message)

    def _init_connect_timer(self):
        self.reset_connect_timer()

        def _timeout():
            self.on_unable_to_connect('spawn event not received within 5 seconds')

        self._connect_timeout = Timer(5.0, _timeout)
        self._connect_timeout.start()

    def reset_connect_timer(self):
        if hasattr(self, '_connect_timeout') and self._connect_timeout is not None:
            self._connect_timeout.cancel()
            self._connect_timeout = None

    def _bind_events(self):
        @On(self._bot, 'chat')
        def _on_chat(this, username, message, *rest):
            self.on_chat(username, message)
        @On(self._bot, 'end')
        def _on_end(this, reason, *rest):
            self.on_end(reason)
        @On(self._bot, 'error')
        def _on_error(this, error, *rest):
            self.on_error(error)

        @On(self._bot, 'spawn')
        def _on_spawn(this):
            self.reset_connect_timer()
            self.on_spawn()

        @On(self._bot, 'login')
        def _on_login(this):
            self.on_login()

        # keep a reference so the handler is not garbage-collected
        self._on_chat = _on_chat
        self._on_end = _on_end
        self._on_error = _on_error
        self._on_spawn = _on_spawn
        self._on_login = _on_login

    def run(self):
        super().run()