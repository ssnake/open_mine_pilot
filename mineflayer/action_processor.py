import queue
import asyncio

class ActionProcessor:
    def __init__(self, client):
        self._client = client
        self._action_queue = queue.Queue()

    def whisper(self, username: str, message: str):
        self._action_queue.put(('whisper', (username, message)))

    def say(self, message: str):
        self._action_queue.put(('say', message))

    def answer_master(self, message: str):
        """Answer the master using either whisper or say depending on client config."""
        if getattr(self._client, 'use_say_for_chat', False):
            self.say(message)
        else:
            self.whisper(self._client._master_username, message)

    def enqueue_chat(self, message: str, trace_id: str):
        self._action_queue.put(('call_agent', ('chat', (message, trace_id))))

    def enqueue_system_event(self, event_name: str, message: str, trace_id: str):
        self._action_queue.put(('call_agent', ('system_event', (event_name, message, trace_id))))

    def has_incoming_agent_events(self) -> bool:
        items = list(self._action_queue.queue)
        for item in items:
            action_type, _ = item
            if action_type == 'call_agent':
                return True
        return False

    def handle_chat(self, message: str, trace_id: str):
        result = asyncio.run(self._client.agent.call_async(message, trace_id))
        if result:
            self.answer_master(result)

    def handle_system_event(self, event_name: str, message: str, trace_id: str):
        if not self._client.agent.state_machine.filter_event(event_name, trace_id):
            return
        
        formatted_message = f"[SYSTEM EVENT: {event_name}] {message}"
        result = asyncio.run(self._client.agent.call_async(formatted_message, trace_id))
        if result:
            self.answer_master(result)

    def process_next(self):
        try:
            action_type, args = self._action_queue.get_nowait()
            if action_type == 'whisper':
                username, message = args
                self._client.bot.whisper(username, message)
            elif action_type == 'say':
                self._client.bot.chat(args)
            elif action_type == 'call_agent':
                event_type, args = args
                if event_type == 'chat':
                    self.handle_chat(*args)
                elif event_type == 'system_event':
                    self.handle_system_event(*args)
        except queue.Empty:
            pass
