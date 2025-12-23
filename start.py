from open_mine_pilot import MineflayerTransport    
from dotenv import load_dotenv
load_dotenv()

pilot1 = MineflayerTransport(host='localhost', port=25565, username='bot')
#pilot1.run()
pilot2 = MineflayerTransport(host='localhost', port=25565, username='bot2')
pilot2.run()