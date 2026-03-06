from typing import Any
from .base import Base
from javascript import require

class MineTool(Base):
    def __init__(self, client):
        super().__init__(client)
        self._targetDigBlock = None
    
    def dig_time(self, x: int, y: int, z: int) -> dict[str, Any]:
        """
        Calculates how long it will take to dig a block at the given coordinates.
        
        Args:
            x (int): X coordinate of the block.
            y (int): Y coordinate of the block.
            z (int): Z coordinate of the block.
            
        Returns:
            dict[str, Any]: Status of the operation and the calculated time in milliseconds.
        """
        target_pos = self._to_vec3({'x': x, 'y': y, 'z': z})
        block = self._bot.blockAt(target_pos)
        
        if not block:
            return self._result(False, "No block found at the given coordinates.")
            
        if getattr(block, 'name', '') == 'air':
            return self._result(False, "The block at the given coordinates is 'air'. Air cannot be dug.")
            
        time_to_dig = self._bot.digTime(block)
        return self._result(True, "Calculated dig time", time_ms=time_to_dig)

    def async_start_dig(self, x: int, y: int, z: int) -> dict[str, Any]:
        """
        Starts digging a block at the given coordinates.
        This is an asynchronous operation. 
        You MUST WAIT for a `[SYSTEM EVENT: diggingCompleted]` or `[SYSTEM EVENT: diggingAborted]` before taking your next action. 
        Do not call any other tools until you receive this event.
        
        Args:
            x (int): X coordinate of the block to dig.
            y (int): Y coordinate of the block to dig.
            z (int): Z coordinate of the block to dig.
            
        Returns:
            dict[str, Any]: Status of the operation indicating if digging started successfully.
        """
        target_pos = self._to_vec3({'x': x, 'y': y, 'z': z})
        block = self._bot.blockAt(target_pos)
        
        if not block:
            return self._result(False, "No block found at the given coordinates.")
            
        if getattr(block, 'name', '') == 'air':
            return self._result(False, "The block at the given coordinates is 'air'. You cannot dig air.")

        if self._targetDigBlock:
            return self._result(False, "Already digging another block. Call stop_dig first.")

        try:
            # We don't await this as it's meant to be an ongoing action
            # The completion will be handled by events
            self._bot.dig(block)
            self._targetDigBlock = block
            
            # Set state to expect digging event
            self._state_machine.set_state(self._state_machine.STATE_EXPECT_DIGGING)
            
            return self._result(True, f"Started digging block `{block.name}`")
        except Exception as e:
            return self._result(False, f"Failed to start digging: {str(e)}")

    def stop_dig(self) -> dict[str, Any]:
        """
        Stops digging the current block.
        
        Returns:
            dict[str, Any]: Status of the operation indicating if digging was stopped successfully.
        """
        if not self._targetDigBlock:
            return self._result(False, "Not currently digging any block.")
            
        self._bot.stopDigging()
        self._targetDigBlock = None
        return self._result(True, f"Stopped digging block")


    def available_methods(self):
        return [self.async_start_dig, self.stop_dig, self.dig_time]
