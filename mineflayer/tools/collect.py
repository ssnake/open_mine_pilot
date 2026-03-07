from typing import Any
from .base import Base
from javascript import AsyncTask, require
import time

class CollectTool(Base):
    def async_collect_drops(self, x: int, y: int, z: int, search_radius: float = 3.0) -> dict[str, Any]:
        """
        Looks for dropped items around the specified coordinates and moves to collect them.
        This is an asynchronous operation. You MUST WAIT for a `[SYSTEM EVENT: collectionCompleted]`
        or `[SYSTEM EVENT: collectionAborted]` before taking your next action.
        
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
                    self._state_machine._agent.get_active_trace_id() if hasattr(self._state_machine, '_agent') and hasattr(self._state_machine._agent, 'get_active_trace_id') else "system"
                )
                
            except Exception as e:
                print(f"Error during async collect: {e}")
                self._client.action_processor.enqueue_system_event(
                    'collectionAborted', 
                    f"Collection failed: {str(e)}", 
                    self._state_machine._agent.get_active_trace_id() if hasattr(self._state_machine, '_agent') and hasattr(self._state_machine._agent, 'get_active_trace_id') else "system"
                )
                
        # Set state to expect collection completion
        self._state_machine.set_state(self._state_machine.STATE_EXPECT_COLLECTION)
        
        return self._result(True, f"Started pathing to collect {len(target_items)} dropped items near {x}, {y}, {z}")

    def available_methods(self):
        return [self.async_collect_drops]
