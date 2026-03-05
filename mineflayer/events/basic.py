from javascript import On, AsyncTask

class BasicEvents:
    def __init__(self, client):
        self._client = client
        self._bot = client._bot
        self._handlers = []

    def _log(self, message):
        print(f"[Events]: {message}")

    def bind(self):
        @On(self._bot, 'chat')
        def on_chat(this, username, message, *rest):
            self._log(f'Chat: {username}: {message}')
            if username == self._client._master_username:
                self._client.agent.enqueue_chat(message)

        @On(self._bot, 'end')
        def on_end(this, reason, *rest):
            self._log(f'End: {reason}')

        @On(self._bot, 'error')
        def on_error(this, error, *rest):
            self._log(f'Error: {error}')

        @On(self._bot, 'spawn')
        def on_spawn(this):
            self._log('Spawn')
            # self._client._reassure_viewer()
            self._client._set_state(self._client.STATE_CONNECTED)
            self._client._reset_connect_timer()

        @On(self._bot, 'login')
        def on_login(this):
            self._log('Login')
        
        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_chat, on_end, on_error, on_spawn, on_login]
