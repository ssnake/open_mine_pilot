from javascript import On, AsyncTask

class MineEvents:
    def __init__(self, client):
        self._client = client
        self._bot = client._bot
        self._handlers = []

    def _log(self, message):
        print(f"[MineEvents]: {message}")

    def bind(self):
        @On(self._bot, 'diggingCompleted')
        def on_digging_completed(this, block):
            self._log(f'Finished digging block at {block.position.x}, {block.position.y}, {block.position.z}')
            self._client.tools._mine_tool._targetDigBlock = None
            self._client.agent.enqueue_system_event('diggingCompleted', f'Finished digging block `{block.name}` at {block.position.x}, {block.position.y}, {block.position.z}')
                

        @On(self._bot, 'diggingAborted')
        def on_digging_aborted(this, block):
            self._log(f'Digging aborted for block `{block.name}` at {block.position.x}, {block.position.y}, {block.position.z}')
            self._client.tools._mine_tool._targetDigBlock = None
            self._client.agent.enqueue_system_event('diggingAborted', f'Digging aborted for block {block.name}')

        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_digging_completed, on_digging_aborted]
