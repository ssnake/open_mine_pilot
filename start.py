from open_mine_pilot import MineflayerPilot    

pilot1 = MineflayerPilot(host='localhost', port=25565, username='bot')
pilot1.run()
pilot2 = MineflayerPilot(host='localhost', port=25565, username='bot2')
pilot2.run()