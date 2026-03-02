import math
from typing import Any
from .base import Base
from javascript import require

pathfinder = require("mineflayer-pathfinder")
Vec3 = require("vec3").Vec3

class MovementTools(Base):
    def __init__(self, bot):
        super().__init__(bot)
        self._follow_master = None
        
    def available_methods(self):
        method_names = [
            "get_my_position",
            "get_my_orientation",
            "set_my_orientation",
            "goto_position",
            "stop_pathing",
            "get_player_position",
            "follow_player",
            "stop_following",
        ]
        return [getattr(self, name) for name in method_names]            
    
    def get_player_position(self, username: str) -> dict[str, float]:
        """
        Get player position

        Args:
            username (str): Player name 

        Returns:
            dict[str, Any]: Player position {'x','y','z'} on success, or an error result.
        """
        entity = self._get_player_entity(username)
        if not entity:
            return self._result(False, f"Player '{username}' is not visible")
        return self._pos_to_dict(entity.position)
    
    def get_my_position(self) -> dict[str, float]:
        """
        Return the bot's current position.

        Returns:
            dict[str, float]: Bot position with keys {'x','y','z'}.
        """
        return self._pos_to_dict(self._bot.entity.position)

    def get_my_orientation(self) -> dict[str, float]:
        """
        Return the bot's current orientation.
        yaw/pitch are in radians.
        yaw uses this tool's external convention, corrected from mineflayer by 180 degrees.

        Useful when you need to reason about where the bot is currently facing
        before calling set_my_orientation.

        Returns:
            dict[str, float]: Orientation with keys {'yaw','pitch'} in radians.
        """
        bot_yaw = float(getattr(self._bot.entity, "yaw", 0.0))
        pitch = float(getattr(self._bot.entity, "pitch", 0.0))
        yaw = self._normalize_angle(bot_yaw - math.pi)
        return {
            "yaw": yaw,
            "pitch": pitch
        }

    def set_my_orientation(
        self,
        yaw: float,
        pitch: float,
        force: bool = True,
    ) -> dict[str, Any]:
        """
        Set the bot's look orientation immediately.

        Args:
            yaw (float): Horizontal angle (radians, external tool convention).
            pitch (float): Vertical angle (radians by default).
            force (bool, optional): Force immediate look update. Defaults to True.

        Notes for agent usage:
            - This tool is synchronous and returns immediately.
            - After calling this tool successfully, provide a short final text response
              to the user (for example: "I'm looking at you now.").

        Returns:
            dict[str, Any]: Standard success/error result with echoed yaw/pitch.
        """
        bot_yaw = self._normalize_angle(float(yaw) + math.pi)
        self._bot.look(bot_yaw, float(pitch), bool(force))
        return self._result(
            True,
            "Orientation was updated successfully",
            yaw=float(yaw),
            pitch=float(pitch),
        )

    def stop_pathing(self) -> dict[str, Any]:
        """
        Stop the current pathfinding action immediately.

        Returns:
            dict[str, Any]: Standard success/error result.
        """
        self._bot.pathfinder.stop()
        return self._result(True, "Pathing stopped")

    def goto_position(self, x: int, y: int, z: int, radius: int = 1) -> dict[str, Any]:
        """
        Navigate near an absolute block position

        Args:
            x (int): Target X coordinate.
            y (int): Target Y coordinate.
            z (int): Target Z coordinate.
            radius (int, optional): Acceptable distance from target. Defaults to 1.

        Returns:
            dict[str, Any]: Standard success/error result with target and radius.
        """

        target = Vec3(int(x), int(y), int(z))
        goal = pathfinder.goals.GoalNear(target.x, target.y, target.z, int(radius))
        self._bot.pathfinder.setGoal(goal)
        return self._result(True, "Goal target is set successfully. You're on the way!", target=self._pos_to_dict(target), radius=int(radius))

    def follow_player(self, username: str, distance: int = 2) -> dict[str, Any]:
        """
        Follow a visible player continuously.

        Args:
            username (str): Player name to follow.
            distance (int, optional): Follow distance in blocks. Defaults to 2.

        Returns:
            dict[str, Any]: Standard success/error result with follow distance.
        """
        entity = self._get_player_entity(username)
        if not entity:
            return self._result(False, f"Player '{username}' is not visible")
        self._follow_master = username
        goal = pathfinder.goals.GoalFollow(entity, int(distance))
        self._bot.pathfinder.setGoal(goal, True)
        return self._result(True, f"Following '{username}'", distance=int(distance))

    def stop_following(self) -> dict[str, Any]:
        """
        Stop following any player.

        Returns:
            dict[str, Any]: Standard success/error result.
        """
        self._follow_master = None
        self._bot.pathfinder.setGoal(None)
        return self._result(True, "Stopped following")        