from typing import Any
from .base import Base
from javascript import AsyncTask, require
import time

class CollectTool(Base):
    def collect_drops(self, x: int, y: int, z: int, search_radius: float = 3.0) -> dict[str, Any]:
        """
        Looks for dropped items around the specified coordinates and moves to collect them.
        This is an asynchronous operation but it will block until collection completes or fails.
        
        Args:
            x (int): X coordinate of the mined block.
            y (int): Y coordinate of the mined block.
            z (int): Z coordinate of the mined block.
            search_radius (float): How far to search for dropped items.
        """
        target_pos = self._to_vec3({'x': x + 0.5, 'y': y + 0.5, 'z': z + 0.5})
        
        # Find all dropped item entities near the location
        entities = self._bot.entities
        target_items = []
        
        for entity_id in entities:
            entity = entities[entity_id]
            # check if entity is a dropped item
            if getattr(entity, 'name', '') == 'item' or getattr(entity, 'displayName', '') == 'Item':
                dist = entity.position.distanceTo(target_pos)
                if dist <= search_radius:
                    target_items.append(entity)
                    
        if not target_items:
            # Nothing to collect, report immediate completion
            return self._result(False, f"No dropped items found within {search_radius} blocks of {x}, {y}, {z}. Collection finished.")
            
        @AsyncTask(start=True)
        def do_collect(task):
            try:
                pathfinder = require('mineflayer-pathfinder')
                Movements = pathfinder.Movements
                goals = pathfinder.goals
                
                mcData = require('minecraft-data')(self._bot.version)
                movements = Movements(self._bot, mcData)
                self._bot.pathfinder.setMovements(movements)
                
                for item_entity in target_items:
                    # Check if entity is still valid before moving to it
                    if not getattr(item_entity, 'isValid', True):
                        continue
                        
                    # Get integer coordinates for GoalBlock
                    pos_x = int(item_entity.position.x)
                    pos_y = int(item_entity.position.y)
                    pos_z = int(item_entity.position.z)
                        
                    goal = goals.GoalBlock(pos_x, pos_y, pos_z)
                    self._bot.pathfinder.setGoal(goal, True)
                    
                    # Wait for pathfinding to reach the entity or timeout
                    start_time = time.time()
                    while time.time() - start_time < 10.0:  # 10 second timeout per item
                        if not getattr(item_entity, 'isValid', True):
                            # Entity picked up or despawned
                            break
                            
                        bot_pos = self._bot.entity.position
                        if bot_pos.distanceTo(item_entity.position) < 1.0:
                            # Close enough
                            break
                            
                        time.sleep(0.5)
                        
                # Ensure pathfinding is stopped after collecting
                self._bot.pathfinder.setGoal(None)
                
                # Emit system event for completion
                self._client.action_processor.enqueue_system_event(
                    'collectionCompleted', 
                    f"Successfully collected {len(target_items)} dropped items.",
                    "system"
                )
                
            except Exception as e:
                print(f"Error during async collect: {e}")
                self._client.action_processor.enqueue_system_event(
                    'collectionAborted', 
                    f"Collection failed: {str(e)}", 
                    "system"
                )
                
        self._client.action_processor.answer_master(f"Started pathing to collect {len(target_items)} dropped items near {x}, {y}, {z}")
        
        event_message = self._client.action_processor.wait_for_events(['collectionCompleted', 'collectionAborted'], timeout=60.0)
            
        if event_message == "":
            self._bot.pathfinder.setGoal(None)
            return self._result(False, "Collection timed out after 60 seconds")
            
        if "error" not in event_message and "aborted" not in event_message.lower() and "failed" not in event_message.lower():
            return self._result(True, f"Successfully collected {len(target_items)} dropped items.")
        else:
            return self._result(False, event_message)

    def available_methods(self):
        return [self.collect_drops]
