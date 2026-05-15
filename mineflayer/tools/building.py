from typing import Any
from .base import Base
from javascript import AsyncTask

class BuildingTool(Base):
    async def place_block(self, reference_x: int, reference_y: int, reference_z: int, face_x: int, face_y: int, face_z: int) -> dict[str, Any]:
        """
        Places a block in the world. The block placed will be whatever is currently equipped in the bot's hand.
        Use inventory.equip_item() first to hold the block you want to place.
        
        This is an asynchronous operation but it will block until placement completes or fails.
        
        Args:
            reference_x (int): X coordinate of the block you are attaching to.
            reference_y (int): Y coordinate of the block you are attaching to.
            reference_z (int): Z coordinate of the block you are attaching to.
            face_x (int): X direction of the face you are placing on (-1, 0, 1).
            face_y (int): Y direction of the face you are placing on (-1, 0, 1). e.g., 1 for top.
            face_z (int): Z direction of the face you are placing on (-1, 0, 1).
        """
        reference_pos = self._to_vec3({'x': reference_x, 'y': reference_y, 'z': reference_z})
        face_vector = self._to_vec3({'x': face_x, 'y': face_y, 'z': face_z})
        
        reference_block = self._bot.blockAt(reference_pos)
        
        if not reference_block:
            return self._result(False, "No reference block found at given coordinates")
            
        if getattr(reference_block, 'name', '') == 'air':
            return self._result(False, "Cannot place block against air. Reference block must be solid.")
            
        bot_pos = self._bot.entity.position
        if bot_pos.distanceTo(reference_pos) > 5:
            return self._result(False, f"Reference block is too far away. You must move closer first.")
            
        target_pos = self._to_vec3({'x': reference_x + face_x, 'y': reference_y + face_y, 'z': reference_z + face_z})
        
        # Calculate distance to center of the target block
        target_center = self._to_vec3({'x': reference_x + face_x + 0.5, 'y': reference_y + face_y + 0.5, 'z': reference_z + face_z + 0.5})
        dist_to_center = bot_pos.distanceTo(target_center)
        
        # Bot is ~0.6 wide and 1.8 tall. If the center of the block is within ~1.2 blocks of our feet, we might be inside it.
        if dist_to_center <= 1.2:
            return self._result(False, "Target position is too close to the bot (distance <= 1.2 blocks). Move away first to avoid placing the block inside yourself.")
            
        # Check if we have an item equipped
        held_item = self._bot.heldItem
        if not held_item:
            return self._result(False, "You must equip a block in your hand first before placing it.")
            

        @AsyncTask(start=True)
        def do_place(task):
            try:
                # We need to ensure the bot isn't trying to place the block inside itself
                # Mineflayer might time out waiting for blockUpdate if the placement is invalid or server ignores it.
                # It throws a JavaScriptError which gets cast to string in Python.
                # We set a large bridge timeout to avoid Python event loop breaking if it hangs.
                self._bot.placeBlock(reference_block, face_vector, timeout=100)
                
                self._client.action_processor.enqueue_system_event(
                    'placementCompleted', 
                    f"Successfully placed {held_item.name} at {reference_x + face_x}, {reference_y + face_y}, {reference_z + face_z}.",
                    "system"
                )
            except Exception as e:
                err_str = str(e)
                if 'did not fire within timeout' in err_str:
                    # If the blockUpdate event doesn't fire, the server likely rejected the placement
                    # (e.g., trying to place it inside the bot's own body). Treat as failure.
                    self._client.action_processor.enqueue_system_event(
                        'placementAborted', 
                        f"Placement failed: The server rejected the placement (timeout waiting for blockUpdate). Did you try to place it inside yourself or in an invalid location?",
                        "system"
                    )
                else:
                    print(f"Error during async place: {err_str}")
                    self._client.action_processor.enqueue_system_event(
                        'placementAborted', 
                        f"Placement failed: {err_str}",
                        "system"
                    )
                
        self._client.action_processor.answer_master(f"Started placing {held_item.name} against block at {reference_x}, {reference_y}, {reference_z}")
        
        event_message = await self._client.action_processor.wait_for_events(['placementCompleted', 'placementAborted'], timeout=15.0)

        if event_message == "":
            return self._result(False, "Placement timed out after 15 seconds")
            
        if "error" not in event_message and "aborted" not in event_message.lower() and "failed" not in event_message.lower():
            return self._result(True, f"Successfully placed {held_item.name} at {reference_x + face_x}, {reference_y + face_y}, {reference_z + face_z}.")
        else:
            return self._result(False, event_message)

    def available_methods(self):
        return [self.place_block]
