from javascript import On, AsyncTask
from .base import Base

class PathfindingEvents(Base):
    def __init__(self, client):
        super().__init__(client)
        self._agent = client.agent
        
    def bind(self):
        @On(self._bot, 'goal_reached')
        def on_goal_reached(this, goal):
            trace_id = self.trace_id()
            msg = 'Mob reached destination'
            self._log(msg, trace_id)
            self._agent.enqueue_system_event('destination_reached', msg, trace_id)


        @On(self._bot, 'path_update')
        def on_path_update(this, data):
            status = data.get('status')
            trace_id = self.trace_id()
            msg = f'path update: {status}'
            self._log(msg, trace_id)
            if status == 'timeout':
                self._agent.enqueue_system_event('destination_path', 'Pathing timed out', trace_id)
            if status == 'noPath':
                self._agent.enqueue_system_event('destination_path', 'No path found', trace_id)
        
        @On(self._bot, 'path_reset')
        def on_path_reset(this, reason):
            trace_id = self.trace_id()
            msg = f'path reset: {reason}'
            self._log(msg, trace_id)
            # self._agent.enqueue_system_event('path_reset', f"Mob is on the path, but path was reset because of reason: {reason}", trace_id)

        @On(self._bot, 'path_stop')
        def on_path_stop(this):
            trace_id = self.trace_id()
            msg = f"Mob is on the path, but pathing was stopped"
            self._log(msg, trace_id)
            self._agent.enqueue_system_event('destination_path', msg, trace_id)
        
        # Keep references so handlers are not garbage-collected.
        self._handlers = [on_goal_reached, on_path_reset, on_path_stop]
