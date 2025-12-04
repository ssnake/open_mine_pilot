from javascript import require, On, Once, AsyncTask, once, off
mineflayer = require('mineflayer')
random_number = id([]) % 1000 # Give us a random number upto 1000
BOT_USERNAME = f'colab_{random_number}'

bot = mineflayer.createBot({ 'host': 'localhost', 'port': 25565, 'username': BOT_USERNAME, 'hideErrors': False })

# The spawn event
once(bot, 'login')
bot.chat('I spawned')