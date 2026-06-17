from tests.mocks.mock_tools import MockTools


class MockClient:
    def __init__(self):
        self.tools = MockTools()
        self._master_username = "master"
