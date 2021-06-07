import re

class door_window:
    def __init__(self, zoneid: int, name: str, state: str, partition_id: int, device_class="door", **kwargs):
        """
        Arguments:
        zoneid: int
        name: str
        state: str
        partition_id: int
        device_class: str = door
        will_topic
        birth_topic
        will_payload = offline
        birth_payload = offline
        """
        self.__c_will_topic__ = "will_topic"
        self.__c_will_payload__ = "will_payload"
        self.__c_birth_topic__ = "birth_topic"
        self.__c_birth_payload__ = "birth_payload"
        self.__c_homeassistant_mqtt_discovery_topic__ = "homeassistant_mqtt_discovery_topic"
        self.__c_mqtt_state_topic__ = "mqtt_state_topic"
        self.__c_mqtt_availability_topic__ = "mqtt_availability_topic"

        self.zoneid = zoneid
        self.friendly_name = name
        self.entity_id = re.sub("\W", "_", self.friendly_name).lower()
        self.state = state
        self.partition_id = partition_id
        self.device_class = device_class
        self.payload_on = "Open"
        self.payload_off = "Closed"
        self.payload_available = "online"
        self.payload_not_available = "offline"
        self.homeassistant_mqtt_discovery_topic = kwargs[self.__c_homeassistant_mqtt_discovery_topic__] if self.__c_homeassistant_mqtt_discovery_topic__ in kwargs else "homeassistant/"
        self.mqtt_state_topic = kwargs[self.__c_mqtt_state_topic__] if self.__c_mqtt_state_topic__ in kwargs else "mqtt-states/"
        self.mqtt_availability_topic = kwargs[self.__c_mqtt_availability_topic__] if self.__c_mqtt_availability_topic__ in kwargs else "mqtt-availability/"

        self.will_topic = kwargs[self.__c_will_topic__] if self.__c_will_topic__ in kwargs else "mqtt-client/status"
        self.birth_topic = kwargs[self.__c_birth_topic__] if self.__c_birth_topic__ in kwargs else "mqtt-client/status"
        self.will_payload = kwargs[self.__c_will_payload__] if self.__c_will_payload__ in kwargs else "offline"
        self.birth_payload = kwargs[self.__c_birth_payload__] if self.__c_birth_payload__ in kwargs else "online"

        self.config_topic = self.homeassistant_mqtt_discovery_topic + ("/" if not self.homeassistant_mqtt_discovery_topic.endswith("/") else "") + "binary_sensor/" + self.entity_id + "/config"
        self.state_topic = self.mqtt_state_topic + "binary_sensor/" + self.entity_id + "/state"
        self.availability_topic = self.mqtt_availability_topic + "binary_sensor/" + self.entity_id + "/availability"

    @property
    def availability_list(self):
        al = [
                {
                    "payload_available": self.payload_available,
                    "payload_not_available": self.payload_not_available,
                    "topic": self.availability_topic
                }
        ]
        if self.birth_topic == self.will_topic:
            al.append(
                {
                    "payload_available": self.birth_payload,
                    "payload_not_available": self.will_payload,
                    "topic": self.will_topic
                }
            )
        return al

    def config_payload(self):
        payload = {
            "name": self.friendly_name,
            "device_class": self.device_class,
            "state_topic": self.state_topic,
            "payload_on": self.payload_on,
            "payload_off": self.payload_off,
            "availability_mode": "all",
            "availability": self.availability_list
        }
        return payload
        
    def __str__(self):
        
        me = ("zoneid: %s, entity_id: %s, friendly_name: %s, state: %s, \
                partition_id: %s, device_class: %s, payload_on: %s, payload_off: %s, \
                config_topic: %s, state_topic: %s, availability: %s" % (self.zoneid, self.entity_id, \
                self.friendly_name, self.state, self.partition_id, self.device_class, \
                self.payload_on, self.payload_off, self.config_topic, self.state_topic, self.availability_list))
        return me
    
    def __repr__(self):
        me = f'{{' \
            f'"zoneid": self.zoneid,' \
            f'"entity_id": self.entity_id,' \
            f'"friendly_name": self.friendly_name,' \
            f'"state": self.state,' \
            f'"partition_id": self.partition_id,' \
            f'"device_class": self.device_class,' \
            f'"payload_on": self.payload_on,' \
            f'"payload_off": self.payload_off,' \
            f'"config_topic": self.config_topic,' \
            f'"state_topic": self.state_topic,' \
            f'"availability": self.availability_list' \
        f'}}'
        return me