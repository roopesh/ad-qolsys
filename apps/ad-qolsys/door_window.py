import re

class door_window:
    def __init__(self, zoneid: int, name: str, state: str, partition_id: int, device_class="door", **kwargs):
        """ Arguments:
        zoneid: int
        name: str
        state: str
        partition_id: int
        device_class: str = door"""
        self.__c_will_topic__ = "will_topic"
        self.__c_will_payload__ = "will_payload"
        self.__c_birth_topic__ = "birth_topic"
        self.__c_birth_payload__ = "birth_payload"
        self.zoneid = zoneid
        self.friendly_name = name
        self.entity_id = re.sub("\W", "_", self.friendly_name).lower()
        self.state = state
        self.partition_id = partition_id
        self.device_class = device_class
        self.payload_on = "Open"
        self.payload_off = "Closed"
        self.config_topic = "homeassistant/binary_sensor/" + self.entity_id + "/config"
        self.state_topic = "mqtt_states/binary_sensor/" + self.entity_id + "/state"
        self.availability_topic = "mqtt_availability/binary_sensor/" + self.entity_id + "/availability"
        self.payload_available = "online"
        self.payload_not_available = "offline"
        self.will_topic = kwargs[self.__c_will_topic__] if self.__c_will_topic__ in kwargs else "mqtt-client/status"
        self.birth_topic = kwargs[self.__c_birth_topic__] if self.__c_birth_topic__ in kwargs else "mqtt-client/status"
        self.will_payload = kwargs[self.__c_will_payload__] if self.__c_will_payload__ in kwargs else "offline"
        self.birth_payload = kwargs[self.__c_birth_payload__] if self.__c_birth_payload__ in kwargs else "online"

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
                config_topic: %s, state_topic: %s" % (self.zoneid, self.entity_id, \
                self.friendly_name, self.state, self.partition_id, self.device_class, \
                self.payload_on, self.payload_off, self.config_topic, self.state_topic))
        return me
    
    def __repr__(self):
        return self.__str__()