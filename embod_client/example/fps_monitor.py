from embod_client import AsyncClient
import argparse
from datetime import datetime
import numpy as np
from uuid import UUID

class FPSMonitor:

    def __init__(self):
        self.times = []

        self.frame_count = 0
        self.max_frame_count = 500

        self.frame_time = np.zeros(self.max_frame_count)
        self.last_time = None

    async def _state_callback(self, state, reward, error):
        """
        This function gets called every time there is a state update from the environment
        :param state: The state of the agent in the environment
        :param reward: The reward from the environment in the current state
        :param error: If there are any errors reported from the environment
        :return:
        """

        current_time = datetime.utcnow()

        if self.last_time is not None:
            time_between = current_time - self.last_time
            self.frame_time[self.frame_count] = time_between.days*86400000 + time_between.seconds*1000 + time_between.microseconds/1000

            if (self.frame_count+1) % 100 == 0:
                average = self.frame_time[max(0, self.frame_count - 100):self.frame_count].mean()
                print("States per second: %.2f" % (1000.0/average))


        # Send an empty state, so the agent does not move anywhere
        await self.client.send_agent_action(np.zeros(3))

        self.last_time = current_time

        self.frame_count += 1

        if self.frame_count == self.max_frame_count:
            self.client.stop()

    def start(self, apikey, agent_id):
        self.client = AsyncClient(apikey, UUID(agent_id), self._state_callback)
        self.client.start()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test frames per second, example application.')
    parser.add_argument('-p', required=True, dest='apikey', help='Your embod.ai API key')
    parser.add_argument('-a', required=True, dest='agent_id', help='The id of the agent you want to control')
    parser.add_argument('-H', default="wss://api.embod.ai", dest='host', help="The websocket host for the environment")

    args = parser.parse_args()

    fps = FPSMonitor()
    fps.start(args.host, args.apikey, args.agent_id)

