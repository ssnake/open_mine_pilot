from javascript import On, AsyncTask
from .base import Base

class BasicEvents(Base):

    def bind(self):
        @On(self._bot, 'chat')
        def on_chat(this, username, message, *rest):
            if username == self._client._master_username:
                trace_id = self.trace_id()
                self._log(f'Chat: {username}: {message}', trace_id)
                self._client.action_processor.chat(message, trace_id)

        @On(self._bot, 'end')
        def on_end(this, reason, *rest):
            self._log(f'End: {reason}', self.trace_id())
            self._client._set_state(self._client.STATE_DISCONNECTED)

        @On(self._bot, 'error')
        def on_error(this, error, *rest):
            self._log(f'Error: {error}', self.trace_id())

        @On(self._bot, 'spawn')
        def on_spawn(this):
            self._log('Spawn', self.trace_id())
            # self._client._reassure_viewer()
            self._client._set_state(self._client.STATE_CONNECTED)
            self._client._reset_connect_timer()

        @On(self._bot, 'login')
        def on_login(this):
            self._log('Login', self.trace_id())
        
        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_chat, on_end, on_error, on_spawn, on_login]
