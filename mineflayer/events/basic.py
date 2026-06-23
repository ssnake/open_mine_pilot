from javascript import On, AsyncTask
from .base import Base

class BasicEvents(Base):

    def bind(self):
        @On(self._bot, 'spawn')
        def on_spawn():
            self._log('Spawn', self.trace_id())
            # self._client._reassure_viewer()
            self._client._set_state(self._client.STATE_CONNECTED)
            self._client._reset_connect_timer()

        @On(self._bot, 'login')
        def on_login():
            self._log('Login', self.trace_id())

        @On(self._bot, 'end')
        def on_end(reason=None, *rest):
            self._log(f'End: {reason}', self.trace_id())
            self._client._set_state(self._client.STATE_DISCONNECTED)

        @On(self._bot, 'error')
        def on_error(error=None, *rest):
            self._log(f'Error: {error}', self.trace_id())

        @On(self._bot, 'chat')
        def on_chat(username=None, message=None, *rest):
            if username == self._client._master_username:
                trace_id = self.trace_id()
                self._log(f'Chat: {username}: {message}', trace_id)
                self._client.action_processor.chat(message, trace_id)

        @On(self._bot, 'messagestr') # for debugging
        def on_messagestr(message=None, position=None, jsonMsg=None, sender=None, *rest):
            trace_id = self.trace_id()
            self._log(f'ServerMessage: {message}', trace_id)
            # self._client.action_processor.chat(message, trace_id)

        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_spawn, on_login, on_end, on_error, on_chat, on_messagestr]
