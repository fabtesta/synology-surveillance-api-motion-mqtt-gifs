import logging
import os
from unittest import TestCase
from unittest.mock import MagicMock, create_autospec

import paho.mqtt.client as mqtt
from paho import mqtt

from services.config import parse_config
from services.mqtt_producer import MqttProducer

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] [%(levelname)s] (%(threadName)-10s) %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


# Define the function that will be tested
def consume_message(client, userdata, message):
    print(f"Received message on topic '{message.topic}': {message.payload.decode()}")


mock_on_message = create_autospec(consume_message)


class TestMqttEvents(TestCase):
    config: dict[str, str]
    gif_filename: str = './resources/gifs/739563.gif'
    gif_filename_decoded: str = './resources/gifs/739563_decoded.gif'

    def setUp(self):
        self.config = parse_config('./resources/config-test.json')
        self.mqtt_producer = MqttProducer(config=self.config)
        if os.path.exists(self.gif_filename_decoded):
            os.remove(self.gif_filename_decoded)

    def test_base64_gif_decoding(self):
        payload = self.mqtt_producer.__encode_to_base64__(self.gif_filename)
        self.mqtt_producer.__decode_from_base64__(payload, self.gif_filename_decoded)
        self.assertTrue(os.path.exists(self.gif_filename_decoded))

    def test_consume_message(self):
        # Create a mock MQTT client
        mock_client = MagicMock(spec=mqtt.client.Client)

        # Set the function to be tested as the on_message callback
        mock_client.on_message = mock_on_message

        # Simulate an incoming MQTT message
        topic = "test/topic"
        payload = self.mqtt_producer.__encode_to_base64__('./resources/gifs/739563.gif')
        message = MagicMock()
        message.topic = topic
        message.payload = payload.encode()

        # Call the on_message callback with the simulated message
        mock_client.on_message(mock_client, None, message)

        # Assert that the consume_message function was called with the correct arguments
        mock_on_message.assert_called_once()
