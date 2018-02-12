# Embod client library

## Dependencies

Embod client library requires python 3.4 or above.

```
pip install -r requirements.txt
```


## AsyncClient

The client uses asyncio to send and recieve action and states respectively from the embod.ai environment.

```python
self.client = AsyncClient(apikey, agent_id, self._state_callback)
self.client.start()
```

**AsyncClient** calls an asynchronous state callback message when there is a new state.
```python
async def _state_callback(self, state, reward, error):
    # Use the state and the reward to calculate the next action
    
    ...
    
    # Send the next action to the environment
    await self.client.send_agent_action(next_action)
```

### Example 

The following example calculates the number of states per second sent by the embod.ai server.

for each state that is sent, an empty action vector is sent back to the server. 
This means the agent will be visible in the environment, but it will not move.

```python

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
        self.client = AsyncClient(apikey, agent_id, self._state_callback)
        self.client.start()


```

