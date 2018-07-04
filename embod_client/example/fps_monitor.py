from embod_client import AsyncClient
import argparse
from datetime import datetime
import numpy as np
from uuid import UUID

class FPSMonitor:

    def __init__(self, agent_ids):
        self._times = []

        self._frame_count = 0
        self._max_frame_count = 500

        self._frame_time = np.zeros(self._max_frame_count)
        self._last_time = None

        self._agent_ids = [UUID(agent_id) for agent_id in agent_ids]


    async def _connect_callback(self):

        for agent_id in self._agent_ids:
            await self.client._add_agent(agent_id)


    async def _state_callback(self, agent_id, state, reward, error):
        """
        This function gets called every time there is a state update from the environment
        :param state: The state of the agent in the environment
        :param reward: The reward from the environment in the current state
        :param error: If there are any errors reported from the environment
        :return:
        """

        if error:
            print("Error: %s" % error.decode('UTF-8'))
            #self.client.stop()
            #return

        current_time = datetime.utcnow()

        if self._last_time is not None:
            time_between = current_time - self._last_time
            self._frame_time[self._frame_count] = time_between.days * 86400000 + time_between.seconds * 1000 + time_between.microseconds / 1000

            if (self._frame_count + 1) % 100 == 0:
                average = self._frame_time[max(0, self._frame_count - 100):self._frame_count].mean()
                print("States per second: %.2f" % (1000.0/average))


        # Send an empty state, so the agent does not move anywhere
        if hasattr(self.client, '_action_size') and self.client._action_size is not None:
            await self.client.send_agent_action(agent_id, np.zeros(self.client._action_size))

        self._last_time = current_time

        self._frame_count += 1

        if self._frame_count == self._max_frame_count:
            for agent_id in self._agent_ids:
                await self.client._remove_agent(agent_id)
            self.client.stop()

    def start(self, apikey, host):
        self.client = AsyncClient(apikey, self._connect_callback, self._state_callback, host)
        self.client.start()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test frames per second, example application.')
    parser.add_argument('-p', required=True, dest='apikey', help='Your embod.ai API key')
    parser.add_argument('-a', required=True, dest='agent_ids', nargs='+', help='The id of the agent you want to control')
    parser.add_argument('-H', default="wss://api.embod.ai", dest='host', help="The websocket host for the environment")

    args = parser.parse_args()

    fps = FPSMonitor(args.agent_ids)
    fps.start(args.apikey, args.host)

