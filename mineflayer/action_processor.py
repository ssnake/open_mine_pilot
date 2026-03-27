import asyncio
from collections import deque
import queue
import threading
import time

class ActionProcessor:
    def __init__(self, client):
        self._client = client
        self._queue = queue.Queue()
        self._expecting_events = queue.Queue()
        
    def _enqueue_action(self, action_type: str, args):
        self._queue.put_nowait((action_type, args))

    def _publish_system_event(self, event_name: str, message: str, trace_id: str):
        formatted_message = f"[SYSTEM EVENT: {event_name}] {message}"
        self._log(formatted_message, trace_id)
        self._expecting_events.put_nowait((event_name, message, trace_id))
    
    async def _handle_chat(self, message: str, trace_id: str):
        result = await self._client.agent.call_async(message, trace_id)
        if result:
            self.answer_master(result)

    async def _handle_system_event(self, event_name: str, message: str, trace_id: str): 
        self._publish_system_event(event_name, message, trace_id)


    async def process_next(self):
        action_type, args = await asyncio.to_thread(self._queue.get)

        if action_type == 'whisper':
            username, message = args
            self._client.bot.whisper(username, message)
        elif action_type == 'say':
            self._client.bot.chat(args)
        elif action_type == 'chat':
           await self._handle_chat(*args)
        elif action_type == 'system_event':
           await self._handle_system_event(*args)


    async def wait_for_events(self, events: list[str], timeout: float) -> str:
       start = time.time()
       while time.time() - start < timeout:
           try:
               event_name, message, trace_id = self._expecting_events.get_nowait()
               if event_name in events:
                   return message
           except queue.Empty:
               pass
           await asyncio.sleep(0.1)
       return ""
    
    def whisper(self, username: str, message: str):
        self._enqueue_action('whisper', (username, message))

    def say(self, message: str):
        self._enqueue_action('say', message)

    def answer_master(self, message: str):
        """Answer the master using either whisper or say depending on client config."""
        if getattr(self._client, 'use_say_for_chat', False):
            self.say(message)
        else:
            self.whisper(self._client._master_username, message)

    def enqueue_chat(self, message: str, trace_id: str):
        self._enqueue_action('chat', (message, trace_id))

    def enqueue_system_event(self, event_name: str, message: str, trace_id: str):
        self._publish_system_event(event_name, message, trace_id)

    def _log(self, message: str, trace_id: str | None = None):
        print(f'[ActionProcessor]:{trace_id} {message}')

