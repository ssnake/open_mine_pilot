from .basic import BasicEvents
from .pathfinding import PathfindingEvents
from .mine import MineEvents

class Events:
    def __init__(self, client):
        self._basic_events = BasicEvents(client)
        self._pathfinding_events = PathfindingEvents(client)
        self._mine_events = MineEvents(client)

    def bind(self):
        self._basic_events.bind()
        self._pathfinding_events.bind()
        self._mine_events.bind()
