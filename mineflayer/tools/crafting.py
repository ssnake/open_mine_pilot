from typing import Any
from .base import Base
from javascript import AsyncTask, require
import time

class CraftingTool(Base):
    def get_recipes_for(self, item_name: str, crafting_table: bool = False) -> dict[str, Any]:
        """
        Gets available recipes for an item, checking if the bot currently has the ingredients.
        
        Args:
            item_name (str): The name of the item to craft (e.g., 'wooden_axe', 'oak_planks').
            crafting_table (bool): Set to True if you intend to use a crafting table. Some items require it.
            
        Returns:
            dict[str, Any]: A list of possible recipes and whether the bot has the ingredients.
        """
        mcData = require('minecraft-data')(self._bot.version)
        
        if item_name not in mcData.itemsByName:
            return self._result(False, f"Item '{item_name}' does not exist in this Minecraft version.")
            
        item_id = mcData.itemsByName[item_name].id
        
        # In Mineflayer, recipesFor(item_id, null, count, craftingTable) returns recipes
        # The second arg is crafting table block, we pass None to just check recipes
        # If we pass a table block, it checks if we have ingredients. We can just pass None and it checks inventory.
        recipes = self._bot.recipesFor(item_id, None, 1, crafting_table)
        
        if not recipes or getattr(recipes, 'length', 0) == 0:
            return self._result(
                False, 
                f"No recipes found for '{item_name}' that you currently have ingredients for. " +
                f"Check your inventory, or try setting crafting_table=True if it requires one."
            )
            
        # Format recipes for the LLM
        formatted_recipes = []
        # In JSPyBridge, arrays have a length property and can be iterated via index
        recipe_length = getattr(recipes, 'length', 0)
        for i in range(recipe_length):
            r = recipes[str(i)] # JS array indexing via string key
            ingredients = []
            if hasattr(r, 'delta'):
                for delta in r.delta:
                    if delta.count < 0: # ingredients are consumed (negative)
                        try:
                            name = mcData.items[delta.id].name
                            ingredients.append(f"{name} x{abs(delta.count)}")
                        except:
                            ingredients.append(f"item_id_{delta.id} x{abs(delta.count)}")
            
            req_table = getattr(r, 'requiresTable', False)
            formatted_recipes.append({
                "recipe_index": i,
                "requires_table": req_table,
                "ingredients": ingredients
            })
            
        return self._result(True, f"Found {recipe_length} recipes for {item_name}", recipes=formatted_recipes)

    def async_craft_item(self, item_name: str, count: int = 1, recipe_index: int = 0, crafting_table_x: int = None, crafting_table_y: int = None, crafting_table_z: int = None) -> dict[str, Any]:
        """
        Craft an item. 
        This is an asynchronous operation. You MUST WAIT for `[SYSTEM EVENT: craftingCompleted]` 
        or `[SYSTEM EVENT: craftingAborted]` before taking your next action.
        
        Before calling this, you should use `get_recipes_for` to ensure you have the ingredients.
        
        Args:
            item_name (str): The name of the item to craft (e.g., 'oak_planks').
            count (int): How many times to craft this recipe. Defaults to 1.
            recipe_index (int): The index of the recipe to use (returned from get_recipes_for). Defaults to 0.
            crafting_table_x (int, optional): X coordinate of crafting table block, if required.
            crafting_table_y (int, optional): Y coordinate of crafting table block, if required.
            crafting_table_z (int, optional): Z coordinate of crafting table block, if required.
        """
        mcData = require('minecraft-data')(self._bot.version)
        
        if item_name not in mcData.itemsByName:
            return self._result(False, f"Item '{item_name}' does not exist in this Minecraft version.")
            
        item_id = mcData.itemsByName[item_name].id
        
        table_block = None
        if crafting_table_x is not None and crafting_table_y is not None and crafting_table_z is not None:
            target_pos = self._to_vec3({'x': crafting_table_x, 'y': crafting_table_y, 'z': crafting_table_z})
            table_block = self._bot.blockAt(target_pos)
            if not table_block or 'crafting_table' not in getattr(table_block, 'name', ''):
                return self._result(False, f"No crafting table found at {crafting_table_x}, {crafting_table_y}, {crafting_table_z}. You must look at one or go near one.")
                
            bot_pos = self._bot.entity.position
            distance = bot_pos.distanceTo(target_pos)
            if distance > 5:
                return self._result(False, f"Crafting table is too far away ({distance:.1f} blocks). You must move closer first (within 5 blocks).")
                
        # Check if we have the recipe
        recipes = self._bot.recipesFor(item_id, None, 1, table_block is not None)
        recipe_length = getattr(recipes, 'length', 0)
        
        if not recipes or recipe_length <= recipe_index:
            return self._result(False, f"Recipe index {recipe_index} is not available for {item_name}. Do you have the required ingredients?")
            
        recipe_to_use = recipes[str(recipe_index)]
        
        @AsyncTask(start=True)
        def do_craft(task):
            try:
                self._bot.craft(recipe_to_use, count, table_block)
                
                self._client.action_processor.enqueue_system_event(
                    'craftingCompleted', 
                    f"Successfully crafted {count}x {item_name}.", 
                    self._state_machine._agent.get_active_trace_id() if hasattr(self._state_machine, '_agent') and hasattr(self._state_machine._agent, 'get_active_trace_id') else "system"
                )
            except Exception as e:
                print(f"Error during async craft: {e}")
                self._client.action_processor.enqueue_system_event(
                    'craftingAborted', 
                    f"Crafting failed: {str(e)}", 
                    self._state_machine._agent.get_active_trace_id() if hasattr(self._state_machine, '_agent') and hasattr(self._state_machine._agent, 'get_active_trace_id') else "system"
                )
                
        # Set state machine to expect crafting completion
        self._state_machine.set_state(self._state_machine.STATE_EXPECT_CRAFTING)
        
        table_msg = "using 2x2 grid" if not table_block else f"using crafting table at {crafting_table_x}, {crafting_table_y}, {crafting_table_z}"
        return self._result(True, f"Started crafting {count}x {item_name} {table_msg}.")

    def available_methods(self):
        return [self.get_recipes_for, self.async_craft_item]
