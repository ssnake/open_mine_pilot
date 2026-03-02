from typing import Any
from .base import Base

class InventoryTools(Base):
    def __init__(self, bot):
        super().__init__(bot)

    def available_methods(self):
        method_names = [
            "list_inventory",
            "equip_item",
            "unequip_item",
            "toss_item",
            "give_item"
        ]
        return [getattr(self, name) for name in method_names]
    
    def list_inventory(self) -> dict[str, Any]:
        """
        Get a list of all items currently in the bot's inventory. If you are in creative mode, you don not need check inventory.

        Returns:
            dict[str, Any]: A result dictionary containing the list of items.
        """
        items = []
        for item in self._bot.inventory.items():
            items.append({
                "name": getattr(item, "name", "unknown"),
                "count": getattr(item, "count", 0),
                "type": getattr(item, "type", 0),
                "slot": getattr(item, "slot", -1)
            })
            
        return self._result(True, "Inventory retrieved", items=items)

    def give_item(self, item_name: str, amount: int = 1) -> dict[str, Any]:
        """
        Give an item to the bot. This command only works in creative mode.

        Args:
            item_name (str): The name of the item to give.
            amount (int, optional): The amount of the item to give. Defaults to 1.

        Returns:
            dict[str, Any]: A result dictionary indicating success or failure.
        """
        try:
            self._bot.chat(f"/give @s {item_name} {amount}")
            return self._result(True, f"Gave {amount} of '{item_name}'")
        except Exception as e:
            return self._result(False, f"Failed to give item: {str(e)}")

    def equip_item(self, item_name: str, destination: str = "hand") -> dict[str, Any]:
        """
        Equip an item from inventory to a specific destination (hand, head, torso, legs, feet, off-hand).
        If you are in creative mode, you can equip items that are not in your inventory.

        Args:
            item_name (str): The name of the item to equip.
            destination (str, optional): Where to equip the item. Defaults to "hand".

        Returns:
            dict[str, Any]: A result dictionary indicating success or failure.
        """
        valid_destinations = ["hand", "head", "torso", "legs", "feet", "off-hand"]
        if destination not in valid_destinations:
            return self._result(False, f"Invalid destination. Must be one of: {', '.join(valid_destinations)}")

        
        item = self._find_inventory_item(item_name)
        if not item:
            return self._result(False, f"Item '{item_name}' not found in inventory")
        
        try:
            self._bot.equip(item, destination)
            return self._result(True, f"Equipped '{item_name}' to {destination}")
        except Exception as e:
            return self._result(False, f"Failed to equip item: {str(e)}")

    def unequip_item(self, destination: str) -> dict[str, Any]:
        """
        Unequip an item from a specific destination.

        Args:
            destination (str): Where to unequip the item from (hand, head, torso, legs, feet, off-hand).

        Returns:
            dict[str, Any]: A result dictionary indicating success or failure.
        """
        valid_destinations = ["hand", "head", "torso", "legs", "feet", "off-hand"]
        if destination not in valid_destinations:
            return self._result(False, f"Invalid destination. Must be one of: {', '.join(valid_destinations)}")

        try:
            self._bot.unequip(destination)
            return self._result(True, f"Unequipped item from {destination}")
        except Exception as e:
            return self._result(False, f"Failed to unequip item: {str(e)}")

    def toss_item(self, item_name: str, count: int = 1) -> dict[str, Any]:
        """
        Toss/drop an item from inventory.

        Args:
            item_name (str): The name of the item to toss.
            count (int, optional): How many to toss. Defaults to 1. Use -1 to toss the whole stack.

        Returns:
            dict[str, Any]: A result dictionary indicating success or failure.
        """
        item = self._find_inventory_item(item_name)
        if not item:
            return self._result(False, f"Item '{item_name}' not found in inventory")

        try:
            if count == -1:
                self._bot.tossStack(item)
                return self._result(True, f"Tossed stack of '{item_name}'")
            else:
                item_type = getattr(item, "type")
                metadata = getattr(item, "metadata", None)
                self._bot.toss(item_type, metadata, count)
                return self._result(True, f"Tossed {count} of '{item_name}'")
        except Exception as e:
            return self._result(False, f"Failed to toss item: {str(e)}")
