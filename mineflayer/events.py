from javascript import On, AsyncTask


class Events:
    def __init__(self, client, bot):
        self._client = client
        self._bot = bot
        self._handlers = []

    def _log(self, message):
        self._client._log(message)

    def bind(self):
        @On(self._bot, 'chat')
        def on_chat(this, username, message, *rest):
            self._log(f'Chat: {username}: {message}')
            if username == 'Server':
                @AsyncTask(start=True)
                def start(task):
                    self._client._tools.handle_message(message)

        @On(self._bot, 'end')
        def on_end(this, reason, *rest):
            self._log(f'End: {reason}')

        @On(self._bot, 'error')
        def on_error(this, error, *rest):
            self._log(f'Error: {error}')

        @On(self._bot, 'spawn')
        def on_spawn(this):
            self._log('Spawn')
            self._client._reassure_viewer()
            self._client._set_state(self._client.STATE_CONNECTED)
            self._client._reset_connect_timer()

        @On(self._bot, 'login')
        def on_login(this):
            self._log('Login')
        
        @On(self._bot, 'goal_reached')
        def on_goal_reached(this, goal):
            self._log('goal reached!!!!')

        @On(self._bot, 'path_update')
        def on_path_update(this, r):
            visited_nodes = r.get('visitedNodes', 0) if isinstance(r, dict) else getattr(r, 'visitedNodes', 0)
            elapsed_ms = r.get('time', 0) if isinstance(r, dict) else getattr(r, 'time', 0)
            path = r.get('path', []) if isinstance(r, dict) else getattr(r, 'path', [])
            path_len = len(path) if hasattr(path, '__len__') else 0
            nodes_per_tick = (visited_nodes * 50 / elapsed_ms) if elapsed_ms else 0
            self._log(
                f"path update: I can get there in {path_len} moves. "
                f"Computation took {elapsed_ms} ms. {visited_nodes} nodes, {nodes_per_tick} nodes/tick"
            )

        @On(self._bot, 'path_reset')
        def on_path_reset(this, reason):
            self._log(f'path reset: {reason}')

        @On(self._bot, 'path_stop')
        def on_path_stop(this):
            self._log('pathing has stopped')
        
        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_chat, on_end, on_error, on_spawn, on_login, on_goal_reached, on_path_update, on_path_reset, on_path_stop]
