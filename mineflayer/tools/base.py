from typing import Any
import math
from javascript import require

pathfinder = require("mineflayer-pathfinder")
Vec3 = require("vec3").Vec3

class Base:
    def __init__(self, client):
        self._client = client
        # Handle cases where just bot is passed for backwards compatibility
        self._bot = getattr(client, 'bot', client)
        self._bot.loadPlugin(pathfinder.pathfinder)
        
        # Note: self._mc_data and self._movements need to be initialized 
        # AFTER the bot has fully spawned and received its version from the server.
        # They will be lazily loaded in the tools when needed.
        self._mc_data_cache = None
        self._movements_cache = None

    @property
    def _mc_data(self):
        if self._mc_data_cache is None:
            self._mc_data_cache = require("minecraft-data")(self._bot.version)
        return self._mc_data_cache

    @property
    def _movements(self):
        if self._movements_cache is None:
            self._movements_cache = pathfinder.Movements(self._bot, self._mc_data)
            self._bot.pathfinder.setMovements(self._movements_cache)
        return self._movements_cache

    @property
    def _state_machine(self):
        return self._client.agent.state_machine

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

    def _normalize_angle(self, angle: float) -> float:
        return (float(angle) + math.pi) % (2 * math.pi) - math.pi

    def _get_block_id(self, block_name: str):
        blocks_by_name = self._mc_data.blocksByName
        
        getter = getattr(blocks_by_name, "get", None)
        if callable(getter):
            block = getter(block_name)
        else:
            try:
                block = blocks_by_name[block_name]
            except Exception:
                block = getattr(blocks_by_name, block_name, None)

        if not block:
            return None
        return block.id

    def _find_inventory_item(self, item_name: str):
        for item in self._bot.inventory.items():
            if getattr(item, "name", None) == item_name:
                return item
        return None

    def _get_player_entity(self, username: str):
        players = getattr(self._bot, "players", None)
        if not players:
            return None

        player = None

        # In python-javascript bridge objects, `.get` may exist but be None/non-callable.
        getter = getattr(players, "get", None)
        if callable(getter):
            player = getter(username)
        else:
            try:
                player = players[username]
            except Exception:
                player = getattr(players, username, None)

        if not player:
            return None
        return getattr(player, "entity", None)
