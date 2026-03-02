from typing import Any
from .base import Base
from .movement import MovementTools

class Tools:
    def __init__(self, bot):
        self._bot = bot
        self._base = Base(bot)
        self._movement_tools = MovementTools(bot)

    def available_methods(self):
        return self._movement_tools.available_methods()       