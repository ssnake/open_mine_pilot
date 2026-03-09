from typing import Any
from .base import Base
from javascript import require, AsyncTask

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

        if getattr(block, 'name', '') in ['water', 'lava']:
            return self._result(False, f"The block is a liquid ({block.name}). You cannot dig liquids.")

        # Check reachability
        bot_pos = self._bot.entity.position
        distance = bot_pos.distanceTo(target_pos)
        if distance > 5:
            return self._result(False, f"Block is too far away ({distance:.1f} blocks). You must move closer first (within 5 blocks).")

        # Check if block is diggable
        if not self._bot.canDigBlock(block):
            return self._result(False, f"Cannot dig block '{block.name}'. You might need a specific tool or it is indestructible.")

        if self._targetDigBlock:
            return self._result(False, "Already digging another block. Call stop_dig first.")

        try:
            # bot.dig returns a Promise in JS. We must run it as an AsyncTask 
            # so JSPyBridge doesn't block the Python main thread waiting for it.
            # If it blocks, diggingCompleted/diggingAborted events will never fire.
            @AsyncTask(start=True)
            def do_dig(task):
                try:
                    # Provide a long timeout (e.g. 100 seconds) so the JSPyBridge does not timeout internally.
                    # Mining obsidian takes a long time, and the bridge default timeout is 10s.
                    self._bot.dig(block, timeout=100)
                except Exception as e:
                    print(f"Error during async dig: {e}")
                    self._client.action_processor.enqueue_system_event(
                        'diggingAborted', 
                        f"Digging failed due to error: {str(e)}", 
                        self._state_machine._agent.get_active_trace_id() if hasattr(self._state_machine, '_agent') and hasattr(self._state_machine._agent, 'get_active_trace_id') else "system"
                    )
            
            self._targetDigBlock = block
            
            # Set state to expect digging event
            self._state_machine.set_state(self._state_machine.STATE_EXPECT_DIGGING)
            
            return self._result(True, f"Started digging block '{block.name}' at {x}, {y}, {z}")
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
