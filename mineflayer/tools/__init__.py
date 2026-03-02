from typing import Any
from .base import Base
from .movement import MovementTools
from .inventory import InventoryTools

class Tools:
    def __init__(self, bot):
        self._bot = bot
        self._base = Base(bot)
        self._movement_tools = MovementTools(bot)
        self._inventory_tools = InventoryTools(bot)

    def available_methods(self):
        return self._movement_tools.available_methods() + self._inventory_tools.available_methods()