from typing import Any
from .base import Base
from .movement import MovementTools
from .inventory import InventoryTools
from .creative import CreativeTools
from .basic import BasicTools
from .mine import MineTool

class Tools:
    def __init__(self, client):
        self._client = client
        self._bot = client.bot
        self._base = Base(client)
        self._movement_tools = MovementTools(client)
        self._inventory_tools = InventoryTools(client)
        self._creative_tools = CreativeTools(client)
        self._basic_tools = BasicTools(client)
        self._mine_tool = MineTool(client)

    def available_methods(self):
        return self._movement_tools.available_methods() + self._inventory_tools.available_methods() + self._creative_tools.available_methods() + self._basic_tools.available_methods() + self._mine_tool.available_methods()