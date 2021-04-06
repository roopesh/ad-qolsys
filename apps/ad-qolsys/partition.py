import re

class partition:
    def __init__(self, p_id: int, name: str, status: str):
        """ Arguments:
        id: int
        name: str
        status: str
        zones: dict"""
        
        self.p_id = p_id
        self.name = name
        self.zones = set()
        self.entity_id = re.sub("\W", "_", self.name).lower()
        self.payload_on = "ARMED"
        self.payload_off = "DISARM"
        self.__c_disarmed__ = "disarmed"
        self.__c_armed_home__ = "armed_home"
        self.__c_armed_away__ = "armed_away"

        self.config_topic = "homeassistant/binary_sensor/" + self.entity_id + "/config"
        self.state_topic = "mqtt_states/binary_sensor/" + self.entity_id + "/state"
        self.alarm_panel_config_topic = "homeassistant/alarm_control_panel/qolsys/" + self.entity_id + "/config"
        self.alarm_panel_state_topic = "mqtt_states/alarm_control_panel/qolsys/" + self.entity_id + "/state"
        self.status = status

    def alarm_config_payload(self):
        payload = {
            "name": self.name,
            "code": 2102,
            "state_topic": self.alarm_panel_state_topic,
            "code_disarm_required": False,
            "code_arm_required": False,
            "command_topic":"qolsys/requests",
            "payload_disarm":'{"event":"DISARM","token":"shw9s8", "usercode":2102, "partition_id":0}',
            "payload_arm_home":'{"event":"ARM", "arm_type":"stay", "token":"shw9s8", "usercode":2102, "partition_id":0}',
            "payload_arm_away":'{"event":"ARM", "arm_type":"away", "token":"shw9s8", "usercode":2102, "partition_id":0}'
        }
        return payload

    def config_payload(self):
        payload = {
            "name": self.name,
            "state_topic": self.state_topic,
            "payload_on": self.payload_on,
            "payload_off": self.payload_off
        }
        return payload

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status:str):
        __c_ARM_STAY__ = "ARM_STAY"
        __c_ARM_DELAY__ = "EXIT_DELAY"
        __c_DISARM__ = "DISARM"
        valid_values = {__c_ARM_STAY__, __c_ARM_DELAY__, __c_DISARM__}
        if not status in valid_values:
            raise ValueError("Not a valid status: '" + status + "' not in " + str(valid_values))
        elif status in {__c_ARM_STAY__}:
            # self.__status = self.payload_on
            self.__status = self.__c_armed_home__
        elif status in {__c_ARM_DELAY__}:
            self.__status = self.__c_armed_away__
        elif status in {__c_DISARM__}:
            # self.__status = self.payload_off
            self.__status = self.__c_disarmed__
        else:
            raise ValueError("Not sure why it wouldn't set the status")
    
    def add_zone(self, zoneid: int):
        if int(zoneid):
            if not zoneid in self.zones:
                self.zones.add(zoneid)

    def remove_zone(self, zoneid:int):
        if int(zoneid):
            if zoneid in self.zones:
                self.zones.remove(zoneid)

    def __str__(self):
        
        me = ("id: %s, name: %s, status: %s, entity_id: %s, payload_on: %s, payload_off: %s, \
                config_topic: %s, state_topic: %s, zones: %s" % (self.p_id, self.name, self.status, self.entity_id, \
                self.payload_on, self.payload_off, self.config_topic, self.state_topic, self.zones))
        return me
    
    def __repr__(self):
        return self.__str__()