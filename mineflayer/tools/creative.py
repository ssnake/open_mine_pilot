from javascript import require
from .base import Base

class CreativeTools(Base):
    def __init__(self, bot):
        super().__init__(bot)
        self._Item = require("prismarine-item")(bot.version)

    def set_inventory_slot(self, slot: int, item_name: str, count: int = 1):
        """
        Gives the bot the specified item in the specified inventory slot.
        This only works in creative mode.
        
        Args:
            slot (int): The inventory window coordinate (e.g., 36 is the first quickbar slot).
            item_name (str): The minecraft ID of the item (e.g., 'diamond_sword'). If None, clears the slot.
            count (int): The number of items to place in the slot. Defaults to 1.
            
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            if item_name is None:
                self._bot.creative.setInventorySlot(slot, None)
                return self._result(True, f"Cleared slot {slot}")
            
            # Remove minecraft: prefix if present
            clean_item_name = item_name.replace("minecraft:", "")
            
            try:
                item_data = self._mc_data.itemsByName[clean_item_name]
            except Exception:
                item_data = getattr(self._mc_data.itemsByName, clean_item_name, None)

            if not item_data:
                return self._result(False, f"Item '{item_name}' not found in registry")
            
            # Clamp count to max stack size to avoid server ignoring the packet and causing timeout
            max_stack_size = getattr(item_data, "stackSize", 64)
            if count > max_stack_size:
                count = max_stack_size
            
            item = self._Item(item_data.id, count)
            self._bot.creative.setInventorySlot(slot, item)
            return self._result(True, f"Set slot {slot} to {count}x {item_name}")
        except Exception as e:
            err_str = str(e)
            if "cancelled due to calling" in err_str:
                return self._result(False, "Failed to set slot: Operation cancelled because another update for this slot is in progress.")
            elif "timeout" in err_str.lower():
                return self._result(False, "Failed to set slot: Server did not respond. The bot is likely NOT actually in Creative mode, or the slot is invalid.")
            return self._result(False, f"Failed to set slot: {e}")

    def clear_slot(self, slot: int):
        """
        Sets the item in the specified slot to null, clearing it.
        This only works in creative mode.
        
        Args:
            slot (int): The inventory window coordinate to clear (e.g., 36 is the first quickbar slot).
            
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            self._bot.creative.clearSlot(slot)
            return self._result(True, f"Cleared slot {slot}")
        except Exception as e:
            return self._result(False, f"Failed to clear slot: {e}")

    def clear_inventory(self):
        """
        Clears the bot's entire inventory.
        This only works in creative mode.
        
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            self._bot.creative.clearInventory()
            return self._result(True, "Cleared inventory")
        except Exception as e:
            return self._result(False, f"Failed to clear inventory: {e}")

    def fly_to(self, x: float, y: float, z: float):
        """
        Moves the bot at a constant speed through 3D space in a straight line to the destination.
        This operation will not work if there is an obstacle in the way, so it is advised to fly very short distances at a time.
        Does not attempt pathfinding. Use this to move < 2 blocks at a time.
        This only works in creative mode.
        
        Args:
            x (float): The x coordinate of the destination.
            y (float): The y coordinate of the destination.
            z (float): The z coordinate of the destination.
            
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            vec = self._to_vec3({"x": x, "y": y, "z": z})
            self._bot.creative.flyTo(vec)
            return self._result(True, f"Flew to {x}, {y}, {z}")
        except Exception as e:
            return self._result(False, f"Failed to fly: {e}")

    def start_flying(self):
        """
        Sets bot.physics.gravity to 0, allowing the bot to hover or fly.
        Useful for hovering while digging the ground below.
        Not necessary to call before fly_to().
        This only works in creative mode.
        
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            self._bot.creative.startFlying()
            return self._result(True, "Started flying")
        except Exception as e:
            return self._result(False, f"Failed to start flying: {e}")

    def stop_flying(self):
        """
        Restores bot.physics.gravity to its original value, making the bot fall normally.
        
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            self._bot.creative.stopFlying()
            return self._result(True, "Stopped flying")
        except Exception as e:
            return self._result(False, f"Failed to stop flying: {e}")

    def available_methods(self):
        return [
            self.set_inventory_slot,
            self.clear_slot,
            self.clear_inventory,
            self.fly_to,
            self.start_flying,
            self.stop_flying
        ]
