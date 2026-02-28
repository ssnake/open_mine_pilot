from javascript import AsyncTask, require
from typing import Any

pathfinder = require("mineflayer-pathfinder")
Vec3 = require("vec3").Vec3


class Tools:
    def __init__(self, bot):
        self._bot = bot
        self._bot.loadPlugin(pathfinder.pathfinder)
        self._mc_data = require("minecraft-data")(bot.version)
        self._movements = pathfinder.Movements(self._bot, self._mc_data)
        self._bot.pathfinder.setMovements(self._movements)
        self._follow_master = None

    def handle_message(self, message):
        if message == "go":
            pos = self.get_my_position()
            target = pos.offset(-100, 0, 0)
            self.goto(target)

    def _result(self, ok: bool, message: str, **extra: Any) -> dict[str, Any]:
        return {
            "status": "success" if ok else "error",
            "message": str(message),
            **extra,
        }

    def _to_vec3(self, point: Any):
        if hasattr(point, "x") and hasattr(point, "y") and hasattr(point, "z"):
            return Vec3(int(point.x), int(point.y), int(point.z))
        if isinstance(point, (list, tuple)) and len(point) == 3:
            return Vec3(int(point[0]), int(point[1]), int(point[2]))
        if isinstance(point, dict) and {"x", "y", "z"}.issubset(point.keys()):
            return Vec3(int(point["x"]), int(point["y"]), int(point["z"]))
        raise ValueError("point must be Vec3, [x,y,z], or {x,y,z}")

    def _pos_to_dict(self, pos) -> dict[str, float]:
        return {"x": float(pos.x), "y": float(pos.y), "z": float(pos.z)}

    def _get_block_id(self, block_name: str):
        block = self._mc_data.blocksByName.get(block_name)
        if not block:
            return None
        return block.id

    def _find_inventory_item(self, item_name: str):
        for item in self._bot.inventory.items():
            if getattr(item, "name", None) == item_name:
                return item
        return None

    def _get_player_entity(self, username: str):
        player = self._bot.players.get(username)
        if not player:
            return None
        return getattr(player, "entity", None)

    def get_my_position(self) -> dict[str, float]:
        """
        Return the bot's current position.
        """
        return self._pos_to_dict(self._bot.entity.position)

    def stop_pathing(self) -> dict[str, Any]:
        """
        Stop the current pathfinding action immediately.
        """
        self._bot.pathfinder.stop()
        return self._result(True, "Pathing stopped")

    def goto(self, point: Any, radius: int = 1) -> dict[str, Any]:
        """
        Navigate near a target coordinate.

        Args:
            point (Any): Target as Vec3, [x, y, z], or {'x','y','z'}.
            radius (int, optional): Acceptable distance from target. Defaults to 1.
        """
        target = self._to_vec3(point)
        goal = pathfinder.goals.GoalNear(target.x, target.y, target.z, int(radius))

        @AsyncTask(start=True)
        async def goto_block(task):
            await self._bot.pathfinder.goto(goal)

        return self._result(True, "Navigating to target", target=self._pos_to_dict(target), radius=int(radius))

    def goto_position(self, x: int, y: int, z: int, radius: int = 1) -> dict[str, Any]:
        """
        Navigate near an absolute block position. This is async tool

        Args:
            x (int): Target X coordinate.
            y (int): Target Y coordinate.
            z (int): Target Z coordinate.
            radius (int, optional): Acceptable distance from target. Defaults to 1.
        """
        return self.goto({"x": x, "y": y, "z": z}, radius=radius)

    def follow_master(self, username: str, distance: int = 2) -> dict[str, Any]:
        """
        Follow a visible player continuously.

        Args:
            username (str): Player name to follow.
            distance (int, optional): Follow distance in blocks. Defaults to 2.
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
        """
        self._follow_master = None
        self._bot.pathfinder.setGoal(None)
        return self._result(True, "Stopped following")

    def mine_block_at(self, x: int, y: int, z: int) -> dict[str, Any]:
        """
        Mine one block at a specific coordinate.

        Args:
            x (int): Block X coordinate.
            y (int): Block Y coordinate.
            z (int): Block Z coordinate.
        """
        target = Vec3(int(x), int(y), int(z))
        block = self._bot.blockAt(target)
        if not block:
            return self._result(False, "No block loaded at target")
        if getattr(block, "name", None) in ("air", "cave_air", "void_air"):
            return self._result(False, "Target is air")
        if not getattr(block, "diggable", False):
            return self._result(False, f"Block '{block.name}' is not diggable")

        @AsyncTask(start=True)
        async def dig_block(task):
            goal = pathfinder.goals.GoalNear(target.x, target.y, target.z, 1)
            await self._bot.pathfinder.goto(goal)
            await self._bot.dig(block)

        return self._result(True, f"Mining block at {x},{y},{z}", block=getattr(block, "name", "unknown"))

    def mine_nearest(self, block_name: str, max_distance: int = 32) -> dict[str, Any]:
        """
        Find and mine the nearest block of a specific type.

        Args:
            block_name (str): Minecraft block id, e.g. 'stone' or 'oak_log'.
            max_distance (int, optional): Search radius in blocks. Defaults to 32.
        """
        block_id = self._get_block_id(block_name)
        if block_id is None:
            return self._result(False, f"Unknown block type '{block_name}'")
        point = self._bot.findBlock({"matching": block_id, "maxDistance": int(max_distance)})
        if not point:
            return self._result(False, f"No '{block_name}' found in range")
        return self.mine_block_at(point.x, point.y, point.z)

    def mine_blocks_at_positions(self, positions: list[Any] | None = None) -> dict[str, Any]:
        """
        Mine blocks at multiple coordinates in sequence.

        Args:
            positions (list[Any], optional): List of positions (Vec3, [x,y,z], or {x,y,z}). Defaults to None.
        """
        if not positions:
            return self._result(False, "No positions provided")

        @AsyncTask(start=True)
        async def mine_many(task):
            for raw in positions:
                pos = self._to_vec3(raw)
                block = self._bot.blockAt(pos)
                if not block:
                    continue
                if getattr(block, "name", None) in ("air", "cave_air", "void_air"):
                    continue
                if not getattr(block, "diggable", False):
                    continue
                goal = pathfinder.goals.GoalNear(pos.x, pos.y, pos.z, 1)
                await self._bot.pathfinder.goto(goal)
                await self._bot.dig(block)

        return self._result(True, "Queued mining for position list", total=len(positions))

    def _find_place_support(self, target_pos):
        faces = [
            Vec3(0, -1, 0),
            Vec3(0, 1, 0),
            Vec3(-1, 0, 0),
            Vec3(1, 0, 0),
            Vec3(0, 0, -1),
            Vec3(0, 0, 1),
        ]
        for face in faces:
            support_pos = target_pos.minus(face)
            support_block = self._bot.blockAt(support_pos)
            if not support_block:
                continue
            if getattr(support_block, "name", None) in ("air", "cave_air", "void_air"):
                continue
            return support_block, face
        return None, None

    def place_block_at(self, x: int, y: int, z: int, item_name: str) -> dict[str, Any]:
        """
        Place a block item at a target coordinate.

        Args:
            x (int): Target X coordinate.
            y (int): Target Y coordinate.
            z (int): Target Z coordinate.
            item_name (str): Inventory item id, e.g. 'cobblestone'.
        """
        target_pos = Vec3(int(x), int(y), int(z))
        target_block = self._bot.blockAt(target_pos)
        if target_block and getattr(target_block, "name", None) not in ("air", "cave_air", "void_air"):
            return self._result(False, "Target position is occupied", occupied_by=target_block.name)

        item = self._find_inventory_item(item_name)
        if not item:
            return self._result(False, f"Item '{item_name}' not found in inventory")

        support_block, face_vector = self._find_place_support(target_pos)
        if not support_block:
            return self._result(False, "No adjacent support block to place against")

        @AsyncTask(start=True)
        async def place(task):
            goal = pathfinder.goals.GoalNear(support_block.position.x, support_block.position.y, support_block.position.z, 2)
            await self._bot.pathfinder.goto(goal)
            await self._bot.equip(item, "hand")
            await self._bot.lookAt(support_block.position.offset(0.5, 0.5, 0.5))
            await self._bot.placeBlock(support_block, face_vector)

        return self._result(
            True,
            f"Placing '{item_name}' at {x},{y},{z}",
            support=self._pos_to_dict(support_block.position),
        )

    def place_blocks_at_positions(self, placements: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """
        Place blocks for multiple coordinate+item entries in sequence.

        Args:
            placements (list[dict], optional): Entries like {'x': int, 'y': int, 'z': int, 'block': str}. Defaults to None.
        """
        if not placements:
            return self._result(False, "No placements provided")

        @AsyncTask(start=True)
        async def place_many(task):
            for placement in placements:
                if isinstance(placement, dict):
                    x = placement.get("x")
                    y = placement.get("y")
                    z = placement.get("z")
                    item_name = placement.get("block") or placement.get("item")
                else:
                    continue
                if x is None or y is None or z is None or not item_name:
                    continue

                target_pos = Vec3(int(x), int(y), int(z))
                target_block = self._bot.blockAt(target_pos)
                if target_block and getattr(target_block, "name", None) not in ("air", "cave_air", "void_air"):
                    continue

                item = self._find_inventory_item(item_name)
                if not item:
                    continue

                support_block, face_vector = self._find_place_support(target_pos)
                if not support_block:
                    continue

                goal = pathfinder.goals.GoalNear(support_block.position.x, support_block.position.y, support_block.position.z, 2)
                await self._bot.pathfinder.goto(goal)
                await self._bot.equip(item, "hand")
                await self._bot.lookAt(support_block.position.offset(0.5, 0.5, 0.5))
                await self._bot.placeBlock(support_block, face_vector)

        return self._result(True, "Queued block placement list", total=len(placements))

    def mine_and_place(
        self,
        mine_positions: list[Any] | None = None,
        place_positions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Run a batch mine phase, then a batch place phase.

        Args:
            mine_positions (list[Any], optional): Positions to mine. Defaults to None.
            place_positions (list[dict], optional): Placement entries with coordinates and block/item name. Defaults to None.
        """
        self.mine_blocks_at_positions(mine_positions)
        self.place_blocks_at_positions(place_positions)
        return self._result(
            True,
            "Queued mine then place workflow",
            mine_total=len(mine_positions or []),
            place_total=len(place_positions or []),
        )

    def available_methods(self) -> list[str]:
        """
        List public tool methods intended for ADK function-calling.
        """
        return [
            "get_my_position",
            "goto_position",
            "stop_pathing",
            "follow_master",
            "stop_following",
            "mine_block_at",
            "mine_nearest",
            "mine_blocks_at_positions",
            "place_block_at",
            "place_blocks_at_positions",
            "mine_and_place",
        ]
