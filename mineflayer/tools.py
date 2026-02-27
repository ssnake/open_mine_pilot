from javascript import require, AsyncTask

pathfinder = require('mineflayer-pathfinder')

class Tools:
    def __init__(self, bot):
        self._bot = bot
        self._bot.loadPlugin(pathfinder.pathfinder)
        mcData = require('minecraft-data')(bot.version)
        self._movements = pathfinder.Movements(self._bot, mcData)
        self._bot.pathfinder.setMovements(self._movements)

    def handle_message(self, message):
        if message == 'go':
            pos = self.get_my_position()
            print(f"my position: {pos}")
            # Never mutate bot.entity.position directly; build a new target position.
            target = pos.offset(-100, 0, 0)
            self.goto(target)

    def goto(self, point):
        print(f"going to: {point}")
        goal = pathfinder.goals.GoalNear(point.x, point.y, point.z, 1)
        # self._bot.pathfinder.setGoal(goal)
        @AsyncTask(start=True)
        def goto_block(task):
            self._bot.pathfinder.setGoal(goal)


    def get_my_position(self):
        """
        Returns the current position of the bot. 
        Vec3. Where
            x - south
            y - up
            z - west
        Functions and methods which require a point argument accept Vec3 instances as well as an array with 3 values, and an object with x, y, and z properties.
        """
        return self._bot.entity.position
