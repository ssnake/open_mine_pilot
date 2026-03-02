from javascript import require, On
import time
from mineflayer.tools.creative import CreativeTools

mineflayer = require('mineflayer')

def main():
    bot = mineflayer.createBot({
        'host': 'localhost',
        'port': 25565,
        'username': 'CreativeBot',
        'hideErrors': False
    })

    # wait for spawn
    @On(bot, 'spawn')
    def handle_spawn(this, *args):
        print("Bot spawned!")
        print(f"Current gamemode: {bot.game.gameMode}")
        
        bot.chat("/gamemode creative")
        
        # Initialize CreativeTools
        creative_tools = CreativeTools(bot)
        run_test(bot)

    @On(bot, 'forcedMove')
    def handle_move(this, *args):
        pass

    test_ran = False

    @On(bot, "game")
    def handle_game_change(this, *args):
        print(f"Gamemode changed to: {bot.game.gameMode}")
        run_test(bot)


    @On(bot, 'error')
    def handle_error(this, err, *args):
        print(f"Bot error: {err}")

    @On(bot, 'kicked')
    def handle_kicked(this, reason, *args):
        print(f"Bot kicked: {reason}")


def run_test(bot):
    if bot.game.gameMode == 'creative':
        # Try to set inventory slot

        print("Attempting to set inventory slot...")
        # Using CreativeTools
        creative_tools = CreativeTools(bot)
        result = creative_tools.set_inventory_slot(5, "minecraft:diamond_helmet", 1)
        print(f"Result (valid): {result}")
        
        bot.quit()

    # Keep python running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
