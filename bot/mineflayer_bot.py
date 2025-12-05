import time
import inspect

from javascript import require, On

from .base import BaseBot

mineflayer = require("mineflayer")


class MineflayerBot(BaseBot):
    def __init__(self, host: str, port: int, username: str):
        super().__init__(host, port, username)
        self._bot = mineflayer.createBot(
            {
                "host": host,
                "port": port,
                "username": username,
                "hideErrors": False,
            }
        )

    def on(self, event: str, handler):
        @On(self._bot, event)
        def _handler(*args, **kwargs):
            sig = inspect.signature(handler)
            param_count = len(sig.parameters)

            # Adapt JS args to the Python handler's expected parameters.
            if param_count == 0:
                return handler()
            elif param_count == 1:
                first_arg = args[0] if args else None
                return handler(first_arg)
            else:
                return handler(*args, **kwargs)

    def chat(self, message: str):
        self._bot.chat(message)

    def run(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
