from javascript import require, On
mineflayer = require('mineflayer')
pathfinder = require('mineflayer-pathfinder')

RANGE_GOAL = 1
BOT_USERNAME = 'python'

bot = mineflayer.createBot({
  'host': '127.0.0.1',
  'port': 25565,
  'username': BOT_USERNAME
})

bot.loadPlugin(pathfinder.pathfinder)
print("Started mineflayer")

@On(bot, 'spawn')
def handle(*args):
  print("I spawned 👋")
  mcData = require('minecraft-data')(bot.version)
  movements = pathfinder.Movements(bot, mcData)
  target =  bot.entity
  if not target:
    bot.chat("I don't see you !")
    return

  pos = target.position
  pos.x += 100
  bot.pathfinder.setMovements(movements)
  bot.pathfinder.setGoal(pathfinder.goals.GoalNear(pos.x, pos.y, pos.z, RANGE_GOAL))

@On(bot, "end")
def handle(*args):
  print("Bot ended!", args)