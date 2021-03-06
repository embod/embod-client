from uuid import UUID
from struct import pack_into, unpack_from
import asyncio
import websockets
import logging
from concurrent import futures

class Client:
    """

    """

    ADD_AGENT = bytes([0])
    REMOVE_AGENT = bytes([1])
    AGENT_ACTION = bytes([2])
    AGENT_STATE = bytes([3])
    AGENT_ADDED = bytes([4])

    ERROR = bytes([255])

    def __init__(self, api_key, connect_callback, state_callback, host="wss://api.embod.ai"):
        """

        :param api_key: api key string
        :param state_callback: callback method for states
        :param host: server hostname, defaults to wss://api.embod.ai
        """

        self._connect_callback = connect_callback

        self._state_callback = state_callback

        self._running = False

        self._logger = logging.getLogger("embod_client")

        self._api_key = api_key

        self._endpoint = host+"/v0/agent/control"

    async def _add_agent(self, agent_id):
        """

        :param agent_id:
        :return:
        """

        await self._send_message_async(Client.ADD_AGENT, agent_id)
        self._logger.info("Adding agent %s to environment" % agent_id)

    async def _remove_agent(self, agent_id):
        """

        :param agent_id:
        :return:
        """

        await self._send_message_async(Client.REMOVE_AGENT, agent_id)
        self._logger.info("Removing agent %s from environment" % agent_id)

    async def send_agent_action(self, agent_id, action):
        """

        :return:
        """

        await self._send_message_async(Client.AGENT_ACTION, agent_id, action)

    async def _start_async(self):

        retries = 0

        while retries < 3:

            try:
                self._websocket = await websockets.connect("%s?apikey=%s" % (self._endpoint, self._api_key), timeout=10)
                self._logger.info("Connected to %s" % self._endpoint)
                self._connected = True
            except websockets.InvalidStatusCode as e:
                self._logger.error("Cannot connect to %s. Status code: %d" % (self._endpoint, e.status_code))
                self._connected = False
                break
            except ConnectionRefusedError as e:
                self._logger.error("Cannot connect to %s" % (self._endpoint))
                self._connected = False

            await self._connect_callback()

            self._running = True

            try:
                timeout_retries = 0
                while self._running:

                    try:
                        message = await asyncio.wait_for(self._websocket.recv(), timeout=1)
                        await self._handle_message_async(message)
                    except futures._base.TimeoutError:
                        timeout_retries += 1
                        self._logger.error("Timeout waiting for message from server")
                        if timeout_retries == 5:
                            if self._websocket is not None:
                                await self._websocket.close()
                            self._connected = False
                            if self._running == False:
                                return

            except websockets.ConnectionClosed as e:
                self._logger.error("Connection closed, cannot recieve more messages")
                retries = 0
            finally:
                if self._websocket is not None:
                    await self._websocket.close()
                self._connected = False
                if self._running == False:
                    return


            retries+=1
            self._logger.error("disconnection detected, retying connection..")
            await asyncio.sleep(1)

    def start(self):
        asyncio.get_event_loop().run_until_complete(self._start_async())

    def stop(self):
        self._running = False

    async def _handle_message_async(self, data):
        """

        :return:
        """

        message_type, resource_id_bytes, message_size = unpack_from('>c16si', data, 0)

        resource_id = UUID(bytes=resource_id_bytes)

        state = None
        error = None
        reward = None

        try:
            if message_type == Client.AGENT_ADDED:
                environment_id_bytes = unpack_from(">16s", data, 21)[0]
                environment_id = UUID(bytes=environment_id_bytes)

                name_length = (message_size - 24)
                environment_name = unpack_from(">%ds" % name_length, data, 37)[0]
                state_size = unpack_from(">i", data, 37 + name_length)[0]
                action_size = unpack_from(">i", data, 37 +name_length + 4)[0]

                self._environment_id = environment_id
                self._environment_name = environment_name.decode('utf-8')
                self._state_size = state_size
                self._action_size = action_size

                self._logger.info("agent added to environment %s:%s" % (str(self._environment_id), self._environment_name))

                print("View your agent here -> https://app.embod.ai/%s/view/%s" % (self._environment_name.lower(), str(resource_id)))
                return

            elif message_type == Client.AGENT_STATE:
                reward = unpack_from(">f", data, 21)[0]
                state_floats = (message_size-4)/4
                state = unpack_from(">%df" % state_floats, data, 25)
            elif message_type == Client.ERROR:
                error = state = unpack_from("%ds" % message_size, data, 21)[0]
        except:
            self._logger.warning("invalid message received")

        await self._state_callback(resource_id, state, reward, error)


    async def _send_message_async(self, message_type, resource_id, data=None):
        """

        :param message_type:
        :param resource_id:
        :param data:
        :return:
        """

        if not self._connected:
            self._logger.error("Cannot send message if loop is not running")
            return

        payload_size = len(data)*4 if data is not None else 0
        buffer_size = 21+payload_size

        buffer = bytearray(buffer_size)

        pack_into("c", buffer, 0, message_type)
        pack_into("16s", buffer, 1, resource_id.bytes)

        if data is not None:
            pack_into(">i", buffer, 17, payload_size)
            pack_into(">%df" % (payload_size/4), buffer, 21, *data)
        else:
            pack_into(">i", buffer, 17, 0)

        await self._websocket.send(bytes(buffer))
