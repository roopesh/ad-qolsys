import re

class partition:
    def __init__(self, p_id: int, name: str, status: str, code: int, confirm_code_arm: bool, confirm_code_disarm: bool, token: str, **kwargs):
        """ Arguments:
        id: int
        name: str
        status: str
        zones: dict"""
        
        self.p_id = p_id
        self.name = name
        self.zones = set()
        self.entity_id = re.sub("\W", "_", self.name).lower()
        # self.payload_on = "ARMED"
        # self.payload_off = "DISARM"
        self.__c_disarmed__ = "disarmed"
        self.__c_armed_home__ = "armed_home"
        self.__c_armed_away__ = "armed_away"
        self.__c_command_topic__ = "command_topic"
        self.__c_will_topic__ = "will_topic"
        self.__c_will_payload__ = "will_payload"
        self.__c_birth_topic__ = "birth_topic"
        self.__c_birth_payload__ = "birth_payload"
        
        self.alarm_panel_config_topic = "homeassistant/alarm_control_panel/qolsys/" + self.entity_id + "/config"
        self.alarm_panel_state_topic = "mqtt_states/alarm_control_panel/qolsys/" + self.entity_id + "/state"
        self.availability_topic = "mqtt_availability/alarm_control_panel/qolsys/" + self.entity_id + "/availability"
        self.status = status
        self.code = code
        self.confirm_code_arm = confirm_code_arm
        self.confirm_code_disarm = confirm_code_disarm
        self.token = token
        self.payload_available = "online"
        self.payload_not_available = "offline"
        self.command_template = '{"event":"{% if action == \"ARM_HOME\" or action == \"ARM_AWAY\" %}ARM","arm_type":"{% if action == \"ARM_HOME\" %}stay{% else %}away{% endif %}"{% else %}{{action}}", "usercode":"' + str(self.code) + '"{% endif %}, "token":"' + self.token + '", "partition_id":"' + str(self.p_id) + '"}'
        self.command_topic = kwargs[self.__c_command_topic__] if self.__c_command_topic__ in kwargs else "qolsys/requests"
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

    def alarm_config_payload(self):
        payload = {
            "name": self.name,
            "state_topic": self.alarm_panel_state_topic,
            "code_disarm_required": self.confirm_code_disarm,
            "code_arm_required": self.confirm_code_arm,
            "command_topic": self.command_topic,
            "command_template": self.command_template,
            "availability_mode": "all",
            "availability": self.availability_list
        }
        if self.confirm_code_disarm or self.confirm_code_arm:
            payload.update({"code": self.code})
        return payload

    # def config_payload(self):
    #     payload = {
    #         "name": self.name,
    #         "state_topic": self.state_topic,
    #         "payload_on": self.payload_on,
    #         "payload_off": self.payload_off
    #     }
    #     return payload

    @property
    def code(self):
        return self.__code

    @code.setter
    def code(self, code: int):
        self.__code = int()
        try:
            if int(code) and len(str(code))>=4:
                self.__code = int(code)
            else:
                raise ValueError("Not a valid code")
        except:
            raise ValueError("Not a valid code")

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
        
        me = ("id: %s, name: %s, status: %s, entity_id: %s, \
                alarm_panel_config_topic: %s, alarm_panel_state_topic: %s, code: %s, zones: %s" % (self.p_id, self.name, self.status, self.entity_id, \
                self.alarm_panel_config_topic, self.alarm_panel_state_topic, self.code, self.zones))
        return me
    
    def __repr__(self):
        return self.__str__()