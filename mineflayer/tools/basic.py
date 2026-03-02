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

    def available_methods(self):
        return [
            self.set_gamemode,
            self.get_gamemode,
            self.set_quick_bar_slot
        ]
