import threading
import uuid

class AgentStateMachine:
    STATE_IDLE = 'idle'
    STATE_EXPECT_DESTINATION = 'expect_destination'
    STATE_EXPECT_DIGGING = 'expect_digging'
    STATE_EXPECT_COLLECTION = 'expect_collection'
    STATE_EXPECT_CRAFTING = 'expect_crafting'
    STATE_EXPECT_PLACEMENT = 'expect_placement'

    def __init__(self, agent=None, log_callback=None):
        self._state = self.STATE_IDLE
        self._agent = agent
        self._log_callback = log_callback
        self._timeout_timer = None
        self._timeout_duration = 60.0

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, new_state: str):
        if self._state != new_state:
            if self._log_callback:
                self._log_callback(f'State changed: {self._state} -> {new_state}', 'system')
            self._state = new_state
            
            # Cancel any existing timer
            self._cancel_timer()
            
            # Start a new timer if not idle
            if new_state != self.STATE_IDLE:
                self._start_timer(new_state)

    def _start_timer(self, expected_state: str):
        def _timeout():
            if self._state == expected_state:
                trace_id = uuid.uuid4()
                if self._log_callback:
                    self._log_callback(f'State timeout: {self._state} after {self._timeout_duration}s', trace_id)
                if self._agent:
                    # Reset state and inject a timeout event
                    self.set_state(self.STATE_IDLE)
                    self._agent._client.action_processor.enqueue_system_event('state_timeout', f'error: State {expected_state} timed out after {self._timeout_duration} seconds', trace_id)

        self._timeout_timer = threading.Timer(self._timeout_duration, _timeout)
        self._timeout_timer.daemon = True
        self._timeout_timer.start()

    def _cancel_timer(self):
        if self._timeout_timer is not None:
            self._timeout_timer.cancel()
            self._timeout_timer = None

    def filter_event(self, event_name: str, trace_id: str) -> bool:
        """
        Returns True if the event should be processed, False if it should be ignored.
        Automatically resets state to IDLE if the expected event is received.
        """
        # Timeout events are generated internally when a state times out and should always be processed
        if event_name == 'state_timeout':
            return True
            
        if self._state == self.STATE_EXPECT_DESTINATION:
            if event_name != 'pathfinding_result':
                if self._log_callback:
                    self._log_callback(f"Ignoring noise event {event_name} while expecting destination", trace_id)
                return False
            # Reset state on relevant event
            self.set_state(self.STATE_IDLE)
            return True
            
        elif self._state == self.STATE_EXPECT_DIGGING:
            if event_name not in ('diggingCompleted', 'diggingAborted'):
                if self._log_callback:
                    self._log_callback(f"Ignoring noise event {event_name} while expecting digging completion", trace_id)
                return False
            # Reset state on relevant event
            self.set_state(self.STATE_IDLE)
            return True
            
        elif self._state == self.STATE_EXPECT_COLLECTION:
            if event_name not in ('collectionCompleted', 'collectionAborted'):
                if self._log_callback:
                    self._log_callback(f"Ignoring noise event {event_name} while expecting collection completion", trace_id)
                return False
            # Reset state on relevant event
            self.set_state(self.STATE_IDLE)
            return True
            
        elif self._state == self.STATE_EXPECT_CRAFTING:
            if event_name not in ('craftingCompleted', 'craftingAborted'):
                if self._log_callback:
                    self._log_callback(f"Ignoring noise event {event_name} while expecting crafting completion", trace_id)
                return False
            # Reset state on relevant event
            self.set_state(self.STATE_IDLE)
            return True
            
        elif self._state == self.STATE_EXPECT_PLACEMENT:
            if event_name not in ('placementCompleted', 'placementAborted'):
                if self._log_callback:
                    self._log_callback(f"Ignoring noise event {event_name} while expecting placement completion", trace_id)
                return False
            # Reset state on relevant event
            self.set_state(self.STATE_IDLE)
            return True
            
        return True
