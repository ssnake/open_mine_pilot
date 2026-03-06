from mineflayer.client import Client

def main():
    client = Client('localhost', 25565, 'test', master_username='snake11235')
    client.run()

if __name__ == "__main__":
    main()
