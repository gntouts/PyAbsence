from who_is_on_my_wifi import who
from time import sleep
from paho.mqtt import client as mqtt_client
from dataclasses import dataclass
from typing import List
from os import environ
import logging
import sys



def getenv(name: str, required: bool) -> str:
    """
    Retrieves the value of the specified environment variable.

    Args:
        name (str): The name of the environment variable.
        required (bool): If True, raises an exception if the variable is not set.

    Returns:
        str: The value of the environment variable.

    Raises:
        Exception: If the environment variable is required but not set.
    """
    value = environ.get(name, "")
    if value == "" and required:
        raise Exception(f"Environment variable \"{name}\" is not set")
    return value


@dataclass
class PyAbsenceConfig:
    """
    Configuration class for PyAbsence application.

    Attributes:
        triggers (List[str]): List of trigger MAC adresses for the PyAbsence application.
        delay (int): Delay in seconds between scans.
        retries (int): Number of consecutive absence detections before sending MQTT message.
        mqqtBroker (str): MQTT broker address.
        mqqtPort (int): MQTT broker port.
        mqttTopic (str): MQTT topic for communication.
        mqttClient (str): MQTT client identifier.

    Note:
        The values for the attributes are retrieved from environment variables.
        Make sure the required environment variables are set before initializing
        an instance of this class using the __init__ method.

    Example:
        config = PyAbsenceConfig()
        print(config.triggers)
        print(config.delay)
        # ... (similar for other attributes)
    """

    triggers: List[str]
    delay: int
    retries: int
    mqttBroker: str
    mqttPort: int
    mqttTopic: str
    mqttClient: str

    def __init__(self) -> None:
        triggers = getenv("PYABS_TRIGGERS", True)
        self.triggers = triggers.split(",")
        self.delay = int(getenv("PYABS_DELAY", True))
        self.retries = int(getenv("PYABS_RETRIES", True))
        self.mqttBroker = getenv("MQTT_BROKER", True)
        self.mqttPort = int(getenv("MQTT_PORT", True))
        self.mqttTopic = getenv("MQTT_TOPIC", True)
        self.mqttClient = getenv("MQTT_CLIENT", True)


class MqttClient:
    """
    MQTT client for publishing messages to an MQTT broker.

    Args:
        mqttBroker (str): The address of the MQTT broker.
        mqttPort (int): The port number of the MQTT broker.
        mqttClient (str): The client identifier for the MQTT client.

    Attributes:
        mqqtBroker (str): The address of the MQTT broker.
        mqqtPort (int): The port number of the MQTT broker.
        mqttClient (str): The client identifier for the MQTT client.

    Note:
        The class uses the Paho MQTT client library for communication.

    Example:
        mqtt_client = MqttClient(mqttBroker="broker_address", mqttPort=1883, mqttClient="client_id")
        mqtt_client.notify(topic="example_topic", msg="Hello, MQTT!")

    """

    def __init__(self, mqttBroker: str, mqttPort: int, mqttClient: str) -> None:
        """
        Initializes the MQTT client.

        Args:
            mqttBroker (str): The address of the MQTT broker.
            mqttPort (int): The port number of the MQTT broker.
            mqttClient (str): The client identifier for the MQTT client.
        """
        self.mqqtBroker = mqttBroker
        self.mqqtPort = mqttPort
        self.mqttClient = mqttClient
        self.__inner__ = mqtt_client.Client(self.mqttClient)

    def __connect__(self):
        self.__inner__.on_connect = MqttClient.on_connect
        self.__inner__.connect(self.mqqtBroker, self.mqqtPort)

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.info("Failed to connect, return code %d\n", rc)

    def __publish__(self, topic: str, msg: str) -> None:
        attempts = 0
        while attempts < 5:
            result = self.__inner__.publish(topic, msg)
            status = result[0]
            if status == 0:
                logging.info(f"Sent `{msg}` to topic `{topic}`")
                break
            logging.info(f"Failed to send message to topic {topic}")
            attempts += 1

    def notify(self, topic: str, msg: str) -> None:
        """
        Notifies the MQTT broker with a message on the specified topic.

        Args:
            topic (str): The MQTT topic to publish to.
            msg (str): The message to publish.
        """
        self.__connect__()
        self.__inner__.loop_start()
        self.__publish__(topic=topic, msg=msg)
        self.__inner__.loop_stop()


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.info("Retrieving config from ENV variables")
    config = PyAbsenceConfig()

    logging.info("Initializing MQTT client")
    mq = MqttClient(mqttBroker=config.mqttBroker,
                    mqttPort=config.mqttPort, mqttClient=config.mqttClient)

    logging.info("Begin watching: " + " ".join(config.triggers))

    absent_count = 0
    notified = False
    while True:
        devices = who()
        mac_addresses = [device[3] for device in devices]
        absent = sum([1 for s in config.triggers if s in mac_addresses]) == 0
        if absent:
            logging.info("Noone is here :(")
            absent_count += 1
        else:
            if notified:
                logging.info("Someone returned!")
            absent_count = 0
            notified = False
        if absent_count > config.retries and not notified:
            notified = True
            logging.info(
                "Everyone is missing for the last 5 minutes, I should turn off stuff")
            mq.notify(config.mqttTopic, "on")
        sleep(config.delay)


if __name__ == "__main__":
    main()
