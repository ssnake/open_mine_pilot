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
            visited_nodes = r.get('visitedNodes', 0) if isinstance(r, dict) else getattr(r, 'visitedNodes', 0)
            elapsed_ms = r.get('time', 0) if isinstance(r, dict) else getattr(r, 'time', 0)
            path = r.get('path', []) if isinstance(r, dict) else getattr(r, 'path', [])
            path_len = len(path) if hasattr(path, '__len__') else 0
            nodes_per_tick = (visited_nodes * 50 / elapsed_ms) if elapsed_ms else 0
            print(
                f"path update: I can get there in {path_len} moves. "
                f"Computation took {elapsed_ms} ms. {visited_nodes} nodes, {nodes_per_tick} nodes/tick"
            )


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
