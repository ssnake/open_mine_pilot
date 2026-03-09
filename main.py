from mineflayer.client import Client
import os

def main():
    use_say = os.getenv('USE_SAY_FOR_CHAT', 'false').lower() in ('true', '1', 't')
    master_username = os.getenv('MASTER_USERNAME', 'snake11235')
    username = os.getenv('BOT_USERNAME', 'test')
    client = Client('localhost', 25565, username, master_username=master_username, use_say_for_chat=True)
    client.run()

if __name__ == "__main__":
    main()
