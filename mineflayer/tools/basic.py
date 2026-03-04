from typing import Any
from javascript import require
from .base import Base

class BasicTools(Base):
    def __init__(self, bot):
        super().__init__(bot)

    def set_gamemode(self, mode: str):
        """
        Sets the game mode of the bot.
        
        Args:
            mode (str): The game mode to set (e.g., 'survival', 'creative', 'adventure', 'spectator').
            
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            self._bot.chat(f"/gamemode {mode}")
            return self._result(True, f"Set gamemode to {mode}")
        except Exception as e:
            return self._result(False, f"Failed to set gamemode: {e}")

    def get_gamemode(self):
        """
        Gets the current game mode of the bot.
        
        Returns:
            str: The current game mode (e.g., 'survival', 'creative', 'adventure', 'spectator').
        """
        try:
            return self._bot.game.gameMode
        except Exception as e:
            return f"Failed to get gamemode: {e}"

    def set_quick_bar_slot(self, slot: int):
        """
        Selects a slot in the hotbar (0-8).
        
        Args:
            slot (int): The hotbar slot to select (0-8).
            
        Returns:
            dict: Status of the operation with a success boolean and message.
        """
        try:
            if not (0 <= slot <= 8):
                return self._result(False, f"Invalid slot {slot}. Must be between 0 and 8.")
            self._bot.setQuickBarSlot(slot)
            return self._result(True, f"Selected hotbar slot {slot}")
        except Exception as e:
            return self._result(False, f"Failed to select hotbar slot: {e}")

    def can_see_block(self, x: int, y: int, z: int) -> dict:
        """
        Check if the bot has line of sight to a block at specific coordinates.
        
        Args:
            x (int): X coordinate of the block.
            y (int): Y coordinate of the block.
            z (int): Z coordinate of the block.
            
        Returns:
            dict: Status of the operation with a boolean indicating if block is visible.
        """
        try:
            target_pos = self._to_vec3({'x': x, 'y': y, 'z': z})
            block = self._bot.blockAt(target_pos)
            if not block:
                return self._result(False, "No block found at given coordinates")
            
            can_see = self._bot.canSeeBlock(block)
            return self._result(True, f"Can see block: {can_see}", can_see=can_see)
        except Exception as e:
            return self._result(False, f"Failed to check visibility: {e}")

    def find_blocks(self, matching: list[str] | str, max_distance: int = 64, count: int = 1) -> dict:
        """
        Find closest blocks matching given names. Use this to locate things like 'oak_log', 'dirt', etc.
        If you need to find "any log", provide a list of all log block names you can think of.
        
        Args:
            matching (list[str] | str): Block name or list of block names to find.
            max_distance (int, optional): Maximum distance to search. Defaults to 64.
            count (int, optional): Maximum number of blocks to find. Defaults to 1.
            
        Returns:
            dict: Status of the operation and list of block positions.
        """
        try:
            if isinstance(matching, str):
                matching = [matching]
                
            block_ids = []
            for name in matching:
                b_id = self._get_block_id(name)
                if b_id is not None:
                    block_ids.append(b_id)
                    
            if not block_ids:
                return self._result(False, f"None of the provided block names were recognized in minecraft-data")
                
            options = {
                'matching': block_ids,
                'maxDistance': max_distance,
                'count': count
            }
            
            blocks = self._bot.findBlocks(options)
            
            if not blocks:
                return self._result(True, f"No matching blocks found within {max_distance} blocks", positions=[])
                
            positions = [self._pos_to_dict(b) for b in blocks]
            return self._result(True, f"Found {len(positions)} matching blocks", positions=positions)
        except Exception as e:
            return self._result(False, f"Failed to find blocks: {e}")

    def available_methods(self):
        return [
            self.set_gamemode,
            self.get_gamemode,
            self.set_quick_bar_slot,
            self.can_see_block,
            self.find_blocks
        ]
