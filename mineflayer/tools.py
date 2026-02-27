from javascript import require, AsyncTask, On

pathfinder = require('mineflayer-pathfinder')

class Tools:
    def __init__(self, bot):
        self._bot = bot
        self._bot.loadPlugin(pathfinder.pathfinder)
        self._bind_events()
        mcData = require('minecraft-data')(bot.version)
        self._movements = pathfinder.Movements(self._bot, mcData)
        self._bot.pathfinder.setMovements(self._movements)

    def _bind_events(self):
        @On(self._bot, 'goal_reached')
        def on_goal_reached(this, goal):
            print('goal reached!!!!')

        @On(self._bot, 'path_update')
        def on_path_update(this, r):
            # print(f"path update: {r}")
            # nodes_per_trick = (r.visitedNodes * 50 / r.time)
            # print(f"path update: I can get there in {r.path.length} moves. Compution took ${r.time} ms. {r.visitedNodes} nodes, {nodes_per_trick} /nodes/tick")
            print(f"path update")

        @On(self._bot, 'path_reset')
        def on_path_reset(this, reason):
            print(f"path reset: {reason}")
        
        @On(self._bot, 'path_stop')
        def on_path_stop(this):
            print("pathing has stopped")

        self._on_goal_reached = on_goal_reached
        self._on_path_update = on_path_update
        self._on_path_reset = on_path_reset
        self._on_path_stop = on_path_stop

    def handle_message(self, message):
        if message == 'go':
            pos = self.get_my_position()
            print(f"my position: {pos}")
            pos.z += 5
            self.goto(pos)

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