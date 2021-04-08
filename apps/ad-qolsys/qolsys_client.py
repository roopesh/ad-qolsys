import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt
import qolsys_socket
import qolsys_requests
import json
import door_window
import partition
import sys

#
# qolsys client to get and send events
#
# Args
# mqtt_namespace: (optional) namespace for mqtt defined in appdaemon.yaml; defaults to ""
# qolsys_host: (Required) IP address or hostname for the qolsys panel
# qolsys_port: (Optional) Port on the qolsys panel to connect to; will default to 12345
# qolsys_token: (Required) Token from the qolsys panel
# request_topic: (Optional) The topic to listen to for commands to the qolsys panel; defaults to qolsys/requests
# qolsys_timeout: (Optional) The timeout (in seconds) to wait for any activity to/from the qolsys panel before disconnecting; defaults to 86400
# qolsys_info_topic: (Optional) The topic to publish qolsys INFO events to; defaults to qolsys/info
# UNUSED? # qolsys_zone_update_topic: (Optional) The topic to publish ZONE_UPDATE events to; defaults to qolsys/zone_event
# qolsys_zone_event_topic: (Optional) The topic to publish ZONE_EVENT events to; defaults to qolsys/zone_event
# qolsys_alarming_event_topic: (Optional) The topic to publish ARMING events to; defaults to qolsys/arming
# qolsys_disarming_event_topic: (Optional) The topic to publish DISARMING events to; defaults to qolsys/disarming
# qolsys_confirm_disarm_code: True/False (Optional) Require the code for disarming
# qolsys_confirm_arm_code: True/False (Optional) Require the code for arming
# qolsys_disarm_code: (Required - if you want to disarm the alarm)

class QolsysClient(mqtt.Mqtt):
    def initialize(self):
        
        # An array of the zones
        self.zones = {}
        self.partitions = {}

        # The names of the arguments configured in apps.yaml
        self.__c_mqtt_namespace__ = "mqtt_namespace"
        self.__c_qolsys_host__ = "qolsys_host"
        self.__c_qolsys_port__ = "qolsys_port"
        self.__c_qolsys_request_topic__ = "request_topic"
        self.__c_qolsys_token__ = "qolsys_token"
        self.__c_qolsys_timeout__ = "qolsys_timeout"
        self.__c_qolsys_info_topic = "qolsys_info_topic"
        self.__c_qolsys_zone_update_topic__ = "qolsys_zone_update_topic"
        self.__c_qolsys_zone_event_topic__ = "qolsys_zone_event_topic"
        self.__c_qolsys_arming_topic = "qolsys_alarming_event_topic"
        self.__c_qolsys_disarming_topic = "qolsys_disarming_event_topic"
        self.__c_qolsys_alarm_status_topic = "qolsys_alarm_status_topic"
        self.__c_qolsys_disarm_code__ = "qolsys_disarm_code"
        self.__c_qolsys_confirm_disarm_code__ = "qolsys_confirm_disarm_code"
        self.__c_qolsys_confirm_arm_code__ = "qolsys_confirm_arm_code"

        # populate some variables we'll need to use throughout our app
        self.mqtt_namespace = self.args[self.__c_mqtt_namespace__] if self.__c_mqtt_namespace__ in self.args else ""
        self.qolsys_host = self.args[self.__c_qolsys_host__]
        self.qolsys_port = self.args[self.__c_qolsys_port__] if self.__c_qolsys_port__ in self.args else 12345
        self.request_topic = self.args[self.__c_qolsys_request_topic__] if self.__c_qolsys_request_topic__ in self.args else "qolsys/requests"
        self.qolsys_token = self.args[self.__c_qolsys_token__]
        self.qolsys_timeout = self.args[self.__c_qolsys_timeout__] if self.__c_qolsys_timeout__ in self.args else 86400
        self.qolsys_info_topic = self.args[self.__c_qolsys_info_topic] if self.__c_qolsys_info_topic in self.args else "qolsys/info"
        self.qolsys_zone_update_topic = self.args[self.__c_qolsys_zone_update_topic__] if self.__c_qolsys_zone_update_topic__ in self.args else "qolsys/zone_update"
        self.qolsys_zone_event_topic = self.args[self.__c_qolsys_zone_event_topic__] if self.__c_qolsys_zone_event_topic__ in self.args else "qolsys/zone_event"
        self.qolsys_arming_event_topic = self.args[self.__c_qolsys_arming_topic] if self.__c_qolsys_arming_topic in self.args else "qolsys/arming"
        self.qolsys_disarming_event_topic = self.args[self.__c_qolsys_disarming_topic] if self.__c_qolsys_disarming_topic in self.args else "qolsys/disarming"
        self.qolsys_alarm_status_topic = self.args[self.__c_qolsys_alarm_status_topic] if self.__c_qolsys_alarm_status_topic in self.args else "qolsys/alarm/status"
        self.qolsys_disarm_code = self.args[self.__c_qolsys_disarm_code__] if self.__c_qolsys_disarm_code__ in self.args else 9999
        self.qolsys_confirm_disarm_code = self.args[self.__c_qolsys_confirm_disarm_code__] if self.__c_qolsys_confirm_disarm_code__ in self.args else False
        self.qolsys_confirm_arm_code = self.args[self.__c_qolsys_confirm_arm_code__] if self.__c_qolsys_confirm_arm_code__ in self.args else False
        
        self.log("qolsys_host: %s, qolsys_port: %s, qolsys_token: %s, qolsys_timeout: %s, request_topic: %s", self.qolsys_host, self.qolsys_port, self.qolsys_token, self.qolsys_timeout, self.request_topic, level="DEBUG")
        self.log("Creating qolsys_socket", level="INFO")
        self.qolsys = qolsys_socket.qolsys(self)

        self.qolsys.create_socket(hostname=self.qolsys_host, port=self.qolsys_port, token=self.qolsys_token, cb=self.qolsys_data_received, timeout=self.qolsys_timeout)

        self.log("QolSys Socket Created", level="INFO")

        # Listen for requests
        mqtt_sub = qolsys_requests.MQTTSubscriber(self, self.qolsys)
        self.log("listener for requests topic: %s", self.request_topic, level="INFO")
        mqtt_sub.listen(mqtt_sub.mqtt_request_received, self.request_topic)

        # Listen for qolsys panel events
        self.log("listener for info topic: %s", self.qolsys_info_topic, level="INFO")
        mqtt_sub.listen(mqtt_sub.mqtt_info_event_received, self.qolsys_info_topic)

        self.log("listener for zone event topic: %s", self.qolsys_zone_event_topic, level="INFO")
        mqtt_sub.listen(mqtt_sub.mqtt_zone_event_event_received, self.qolsys_zone_event_topic)
        
        self.log("listener for zone update topic: %s", self.qolsys_zone_update_topic, level="INFO")
        mqtt_sub.listen(mqtt_sub.mqtt_zone_update_event_received, self.qolsys_zone_update_topic)

        self.log("listener for arming topic: %s", self.qolsys_arming_event_topic, level="INFO")
        mqtt_sub.listen(mqtt_sub.mqtt_arming_event_received, self.qolsys_arming_event_topic)


        # Populate the zones and partitions with an INFO call
        info_payload = {"event":"INFO", "token":self.qolsys_token}
        self.call_service("mqtt/publish", namespace=self.mqtt_namespace, topic=self.request_topic, payload=json.dumps(info_payload))

    def terminate(self):
        try:
            self.qolsys.close_socket()
            self.log("Socket closed")
        except:
            self.log("Error closing socket: %s", sys.exc_info(), level="ERROR")

        try:
            for zone in self.zones:
                self.call_service("mqtt/publish", topic=self.zones[zone].config_topic, namespace=self.mqtt_namespace)
            self.log("Zones removed")
        except:
            self.log("Error publishing empty zone: %s, %s", zone, sys.exc_info(), level="ERROR")

        try:
            for part in self.partitions:
                self.call_service("mqtt/publish", topic=self.partitions[part].alarm_config_topic, namespace=self.mqtt_namespace)
            self.log("Partitions removed")
        except:
            self.log("Error publishing empty partition: %s, %s", part, sys.exc_info(), level="ERROR")

        self.log("Terminated")

    def qolsys_data_received(self, data:dict):
        ''' This is where any json data coming from the qolsys panel will be sent.
        In this case I have the data being published to a mqtt topic, but you can do what you want.
        
            Parameters:
                data: json object containing the output from the qolsys panel'''

        topic = "" #self.event_parent_topic
        jdata = json.loads(data)
        event_type = jdata["event"]
        if event_type == "INFO":
            topic = self.qolsys_info_topic

        if event_type == "ZONE_EVENT":
            zone_event_type = jdata["zone_event_type"]
            # Two types of zone events: ZONE_UPDATE, ZONE_ACTIVE
            # zone_event_type is unused for now
            topic = self.qolsys_zone_event_topic
            # if zone_event_type == "ZONE_UDPATE":
            #     topic = self.qolsys_zone_update_topic

        if event_type == "ARMING":
            arming_type = jdata["arming_type"]
            # Three types of arming: ARM_STAY, EXIT_DELAY, DISARM
            topic = self.qolsys_arming_event_topic

        self.log("publishing %s event to: %s", event_type, topic, level="INFO")
        self.log("data being published: %s", data, level="DEBUG")
        
        self.call_service("mqtt/publish", namespace=self.mqtt_namespace, topic=topic, payload=data)

        # Temporary hack to update partitions based on arming
        # if event_type == "ARMING":
        #     info_payload = {"event":"INFO", "token":self.qolsys_token}
        #     self.call_service("mqtt/publish", namespace=self.mqtt_namespace, topic=self.request_topic, payload=json.dumps(info_payload))

    
    def update_zone(self, zoneid, zone):
        self.zones[zoneid] = zone
    
    def update_partition(self, partition_id, partition):
        self.partitions[partition_id] = partition