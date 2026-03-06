from javascript import require, On
import time
import threading

mineflayer = require('mineflayer')

bot = mineflayer.createBot({
    'host': 'localhost',
    'port': 25565,
    'username': 'testbot'
})

def run_worker():
    import queue
    q = queue.Queue()
    q.put("hello")
    while True:
        task = q.get()
        print("got task")
        bot.whisper('snake11235', 'hello from worker thread')
        print("whispered")
        break

@On(bot, 'spawn')
def on_spawn(this):
    print("Spawned!")
    t = threading.Thread(target=run_worker)
    t.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
