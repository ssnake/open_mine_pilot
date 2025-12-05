from bot import MineflayerBot

bot = MineflayerBot(host='localhost', port=25565, username='test')
bot.on('login', lambda: bot.chat('Hello, world!'))
bot.on('error', lambda e: print(e))
bot.run()