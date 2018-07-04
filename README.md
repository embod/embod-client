# Embod client library

## Dependencies

Embod client library requires python 3.4 or above.

```
pip install -r requirements.txt
```


## AsyncClient

The client uses asyncio to send and recieve action and states respectively from the embod.ai environment.

```python
from embod_client import AsyncClient

self.client = AsyncClient(api_key, self._state_callback)
self.client.start()
```

**AsyncClient** calls an asynchronous state callback message when there is a new state.
```python
async def _state_callback(self, agent_id state, reward, error):
    # Use the state and the reward to calculate the next action
    
    ...
    
    # Send the next action to the environment
    await self.client.send_agent_action(next_action)
```

### Example 

The following example calculates the number of states per second sent by the embod.ai server.

Agents can be added in the `connect_callback` method. This is run as soon as the connection is created to the embod.ai servers.
once connect_callback is called the `AsyncClient` will start and event loop which will stream states back to the `_state_callback` method.

for each state that is sent, actions can be sent back to the server


```python

class FPSMonitor:

    def __init__(self, agent_ids):
        self._times = []

        self._frame_count = 0
        self._max_frame_count = 1000

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


```

## Running FPS test

```
python fps_monitor.py -p [YOUR API KEY] -a [YOUR AGENT ID 1] [YOUR AGENT ID 2] ....
```

## More complex control

This very simple example does not cause the agents to move at all. This is just an example of how to use the client library.

Controllers will typically calculate the actions to send for each agent based on the states that are streamed back.

