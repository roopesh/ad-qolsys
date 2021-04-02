import re

class door_window:
    def __init__(self, zoneid: int, name: str, state: str, partition_id: int, device_class="door"):
        """ Arguments:
        zoneid: int
        name: str
        state: str
        partition_id: int
        device_class: str = door"""
        
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

    def config_payload(self):
        payload = {
            "name": self.friendly_name,
            "device_class": self.device_class,
            "state_topic": self.state_topic,
            "payload_on": self.payload_on,
            "payload_off": self.payload_off
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