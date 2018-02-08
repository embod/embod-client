from uuid import UUID
from struct import pack_into, unpack_from, unpack
from websocket import create_connection
import logging

class Client:
    """

    """
    ADD_AGENT = bytes([0])
    REMOVE_AGENT = bytes([1])
    AGENT_ACTION = bytes([2])
    AGENT_STATE = bytes([3])

    ERROR = bytes([255])

    def __init__(self, apikey, state_callback):
        """

        :param apikey:
        :param state_callback:
        """
        self._websocket = create_connection("ws://dev.embod.ai:8080/v0/agent/control?apikey=%s" % apikey)

        self._state_callback = state_callback

        self._running = False

        self._logger = logging.getLogger("embodclient")

        if self._websocket.getstatus() == 101:
            self._logger.info("Embod client connected.")
            self._connected = True
        else:
            self._logger.error("Could not connect")
            self._connected = False

    def add_agent(self, agent_id):
        """

        :param agent_id:
        :return:
        """

        self._send_message(Client.ADD_AGENT, agent_id)
        self._logger.info("Adding agent %s to environment" % agent_id)

    def remove_agent(self, agent_id):
        """

        :param agent_id:
        :return:
        """

        self._send_message(Client.REMOVE_AGENT, agent_id)
        self._logger.info("Removing agent %s from environment" % agent_id)

    def send_agent_action(self, agent_id, action):
        """

        :return:
        """

        self._send_message(Client.AGENT_ACTION, agent_id, action)


    def run_loop(self):

        if not self._connected:
            self._logger.error("Cannot run loop if websocket is disconnected.")
            return

        self._running = True


        while self._running:
            data = self._websocket.recv()

            self._handle_message(data)

    def stop(self):
        self._running = False


    def _handle_message(self, data):
        """

        :return:
        """

        message_type, resource_id_bytes, message_size = unpack_from('>c16si', data, 0)

        resource_id = UUID(bytes=resource_id_bytes)

        state = None
        error = None
        reward = None

        try:

            if message_type == Client.AGENT_STATE:
                reward = unpack_from(">i", data, 21)[0]
                state = unpack_from(">25f", data, 25)
            elif message_type == Client.ERROR:
                error = state = unpack_from("%ds" % message_size, data, 21)

            self._state_callback(resource_id, state, reward, error)
        except:
            self._logger.info("websocket message error")


    def _send_message(self, message_type, resource_id, data=None):
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

        self._websocket.send_binary(buffer)