from javascript import On, AsyncTask
from .base import Base

class MineEvents(Base):
    def bind(self):
        @On(self._bot, 'diggingCompleted')
        def on_digging_completed(this, block):
            msg = f'Finished digging block at {block.position.x}, {block.position.y}, {block.position.z}'
            trace_id = self.trace_id()
            self._log(msg, trace_id)
            self._client.tools._mine_tool._targetDigBlock = None
            self._client.agent.enqueue_system_event('diggingCompleted', msg, trace_id)
                

        @On(self._bot, 'diggingAborted')
        def on_digging_aborted(this, block):
            msg = f'Digging aborted for block at {block.position.x}, {block.position.y}, {block.position.z}'
            trace_id = self.trace_id()
            self._log(msg, trace_id)
            self._client.tools._mine_tool._targetDigBlock = None
            self._client.agent.enqueue_system_event('diggingAborted', msg, trace_id)

        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_digging_completed, on_digging_aborted]
