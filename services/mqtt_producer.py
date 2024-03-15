import base64
import logging

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


class MqttProducer:
    def __init__(self, config: dict):
        self.config = config
        self.mqtt_client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.mqtt_client.username_pw_set(username=self.config["mqtt_user"], password=self.config["mqtt_pwd"])

    def __encode_to_base64__(self, filename):
        with open(filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string

    def __decode_from_base64__(self, encoded_string, filename):
        with open(filename, "wb") as image_file:
            image_file.write(base64.b64decode(encoded_string))

    def publish_gif_message(self, message_type: str, gif_name: str, gif_path: str, topic: str):
        logging.info(
            'publish_mqtt_message type %s gif %s gif path %s mqtt_server %s mqtt_port %i mqtt_base_topic %s topic_name %s',
            message_type, gif_name, gif_path, self.config["mqtt_server"], self.config["mqtt_port"],
            self.config["mqtt_base_topic"],
            topic)
        gif_message = None
        if message_type == 'base64':
            gif_message = self.__encode_to_base64__(gif_path)
        else:
            gif_message = gif_name

        self.mqtt_client.connect(self.config["mqtt_server"],
                                 self.config["mqtt_port"])
        retcode = self.mqtt_client.publish(
            self.config["mqtt_base_topic"] + "/" + topic, gif_message)
        return retcode
