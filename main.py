from mineflayer.client import Client
from agents.base_agent import BaseAgent

def main():
    client = Client('localhost', 25565, 'test', master_username='snake11235')
    client.run()


if __name__ == "__main__":
    main()
