import time


class Transport:
    STATE_IDLE = 'idle'
    STATE_CONNECTING = 'connecting'
    STATE_CONNECTED = 'connected'
    STATE_DISCONNECTED = 'disconnected'

    def __init__(self, username: str):
        self._username = username
        self._state = self.STATE_IDLE

    @property
    def state(self) -> str:
        return self._state

    def _set_state(self, new_state: str):
        if new_state not in (
            self.STATE_IDLE,
            self.STATE_CONNECTING,
            self.STATE_CONNECTED,
            self.STATE_DISCONNECTED,
        ):
            raise ValueError(f'invalid transport state: {new_state}')
        if self._state != new_state:
            self._log(f'state changed: {self._state} -> {new_state}')
        self._state = new_state

    def on_chat(self, username: str, message: str):
        if self._username == username:
            return
        self._log(f'{username} said: {message}')
        self.say(f'Hello {username}')
        
    def on_end(self, reason: str):
        self._log(f'Connection ended: {reason}')
        self._set_state(self.STATE_DISCONNECTED)

    def on_error(self, error: str):
        self._log(f'Connection error: {error}')

    def on_spawn(self):
        self._log(f'{self._username} spawned')
        self._set_state(self.STATE_CONNECTED)

    def on_login(self):
        self._log(f'{self._username} logged in')
        self._set_state(self.STATE_CONNECTED)

    def on_unable_to_connect(self, reason: str):
        self._log(f'Unable to connect: {reason}')
        self._set_state(self.STATE_DISCONNECTED)

    def say(self, message: str):
        pass

    def run(self):
        try:
            self._log('run')
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
    def _log(self, message: str):
        print(f'{self._username}: {message}')