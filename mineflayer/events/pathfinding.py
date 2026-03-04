from javascript import On, AsyncTask

class PathfindingEvents:
    def __init__(self, client):
        self._client = client
        self._bot = client._bot
        self._agent = client.agent
        self._handlers = []

    def _log(self, message):
        print(f"[Events]: {message}")

    def bind(self):
        @On(self._bot, 'goal_reached')
        def on_goal_reached(this, goal):
            self._log('goal reached!!!!')
            @AsyncTask(start=True)
            def call_agent(task):
                self._agent.game_update('[goto_position tool] Mob reached goal')


        # @On(self._bot, 'path_update')
        # def on_path_update(this, r):
        #     visited_nodes = r.get('visitedNodes', 0) if isinstance(r, dict) else getattr(r, 'visitedNodes', 0)
        #     elapsed_ms = r.get('time', 0) if isinstance(r, dict) else getattr(r, 'time', 0)
        #     path = r.get('path', []) if isinstance(r, dict) else getattr(r, 'path', [])
        #     path_len = len(path) if hasattr(path, '__len__') else 0
        #     nodes_per_tick = (visited_nodes * 50 / elapsed_ms) if elapsed_ms else 0
        #     self._log(
        #         f"path update: I can get there in {path_len} moves. "
        #         f"Computation took {elapsed_ms} ms. {visited_nodes} nodes, {nodes_per_tick} nodes/tick"
        #     )

        @On(self._bot, 'path_reset')
        def on_path_reset(this, reason):
            self._log(f'path reset: {reason}')
            @AsyncTask(start=True)
            def call_agent(task):
                self._agent.game_update(f"[goto_position or follow tools] Mob is on the path, but path was reset because of reason: {reason}")

        @On(self._bot, 'path_stop')
        def on_path_stop(this):
            self._log('pathing has stopped')
            @AsyncTask(start=True)
            def call_agent(task):
                self._agent.game_update(f"[goto_position or follow tools] Mob is on the path, but pathing was stopped")
        
        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_goal_reached, on_path_reset, on_path_stop]
