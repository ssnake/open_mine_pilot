from src.open_mine_pilot import Core, Pilot
from javascript import require, On, Once, AsyncTask, once, off

mineflayer = require('mineflayer')


class MineflayerPilot(Pilot):
    def __init__(self, host: str, port: int, username: str):
        super().__init__(username)
        self._bot = mineflayer.createBot({ 
            'host': host, 
            'port': port, 
            'username': username, 
            'hideErrors': False 
        })
        self._bind_events()
    
    def say(self, message: str):
        self._bot.chat(message)

    def _bind_events(self):
        @On(self._bot, 'chat')
        def _on_chat(this, username, message, *rest):
            self.on_chat(username, message)

        # keep a reference so the handler is not garbage-collected
        self._on_chat = _on_chat


    def run(self):
        once(self._bot, 'login')
        self.say('Hello!')
        # super().run()