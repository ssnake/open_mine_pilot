from mineflayer.client import Client
import asyncio
import os

def main():
    master_username = os.getenv('MASTER_USERNAME', 'snake11235')
    username = os.getenv('BOT_USERNAME', 'test')
    client = Client('localhost', 25565, username, master_username=master_username, use_say_for_chat=True)
    asyncio.run(client.run())

if __name__ == "__main__":
    main()
