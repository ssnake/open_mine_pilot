from typing import Any
from .base import Base
from .movement import MovementTools
from .inventory import InventoryTools
from .creative import CreativeTools
from .basic import BasicTools
from .mine import MineTool

class Tools:
    def __init__(self, bot):
        self._bot = bot
        self._base = Base(bot)
        self._movement_tools = MovementTools(bot)
        self._inventory_tools = InventoryTools(bot)
        self._creative_tools = CreativeTools(bot)
        self._basic_tools = BasicTools(bot)
        self._mine_tool = MineTool(bot)

    def available_methods(self):
        return self._movement_tools.available_methods() + self._inventory_tools.available_methods() + self._creative_tools.available_methods() + self._basic_tools.available_methods() + self._mine_tool.available_methods()