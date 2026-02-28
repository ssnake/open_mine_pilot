from mineflayer.client import Client
from agents.base_agent import BaseAgent

def main():
    client = Client('localhost', 25565, 'test')
    client.run()


if __name__ == "__main__":
    main()
