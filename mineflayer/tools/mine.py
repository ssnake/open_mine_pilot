from typing import Any
from .base import Base
from javascript import require

class MineTool(Base):
    def __init__(self, bot):
        super().__init__(bot)
        self._targetDigBlock = None
    
    def dig_time(self, x: int, y: int, z: int) -> dict[str, Any]:
        """Calculates how long it will take to dig a block at the given coordinates."""
        target_pos = self._to_vec3({'x': x, 'y': y, 'z': z})
        block = self._bot.blockAt(target_pos)
        
        if not block:
            return self._result(False, "No block found at the given coordinates.")
            
        time_to_dig = self._bot.digTime(block)
        return self._result(True, "Calculated dig time", time_ms=time_to_dig)

    def start_dig(self, x: int, y: int, z: int) -> dict[str, Any]:
        """Starts digging a block at the given coordinates."""
        target_pos = self._to_vec3({'x': x, 'y': y, 'z': z})
        block = self._bot.blockAt(target_pos)
        
        if not block:
            return self._result(False, "No block found at the given coordinates.")

        if self._targetDigBlock:
            return self._result(False, "Already digging another block.")

        try:
            # We don't await this as it's meant to be an ongoing action
            # The completion will be handled by events
            self._bot.dig(block)
            self._targetDigBlock = block
            return self._result(True, "Started digging block.")
        except Exception as e:
            return self._result(False, f"Failed to start digging: {str(e)}")

    def stop_dig(self) -> dict[str, Any]:
        """Stops digging the current block."""
        if not self._targetDigBlock:
            return self._result(False, "Not currently digging any block.")
            
        self._bot.stopDigging()
        return self._result(True, "Stopped digging.")

    def available_methods(self):
        return [self.start_dig, self.stop_dig, self.dig_time]
