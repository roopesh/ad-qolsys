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
# qolsys_arm_away_always_instant: True/False (Optional) Set to true if all Arm Away commands should be instant; defaults to False
# homeassistant_mqtt_discovery_topic: homeassistant/ (Optional) The topic Home Assistant is using for MQTT Discovery (homeassistant/ is the default in HA and here)
# mqtt_state_topic: mqtt-states (Optional) The topic to publish state updates to for the alarm_control_panel and binary_sensor (default: mqtt-states)
# mqtt_availability_topic: mqtt-availability (Optional) The topic to publish availability events to for the alarm_control_panel and binary_sensor (default: mqtt-availability)
# qolsys_alarm_triggered_topic: (Optional) The topic to publish triggered events to; defaults to qolsys/alarm/triggered
# qolsys_alarm_pending_topic:  (Optional) The topic to publish pending events to; defaults to qolsys/alarm/pending

# Developer documentation
# This is basically how shit flows:
# Get an event from the qolsys panel (qolsys_client.py) --> QolsysClient.qolsys_data_received.
# The event type and sub event (zone_event_type, arming_type, alarm_type) determine which mqtt queue to publish to.
# That data reciever then publishes to the relevant topic, as defined in the app arugments or default topics.

class QolsysClient(mqtt.Mqtt):
    def get_arg(self, name: str, arr: list, default=None):

        if not name:
            raise ValueError("Need a name of a value")
        if not arr:
            arr = self.args

        ret_value = arr[name] if name in arr else default

        return ret_value

    def fix_topic_name(self, topic_name):
        try:
            if topic_name:
                if topic_name.endswith("/"):
                    return topic_name
                else:
                    return (topic_name + "/")
            else:
                self.log("Not a valid topic: %s", topic_name, level="ERROR")
                raise("Not a valid topic" + str(topic_name))
        except:
            self.log("Unable to fix topic_name: %s, Error: %s", topic_name, sys.exc_info(), level="ERROR")
            return ""

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
        self.__c_qolsys_arm_away_always_instant__ = "qolsys_arm_away_always_instant"
        self.__c_homeassistant_mqtt_discovery_topic__ = "homeassistant_mqtt_discovery_topic"
        self.__c_mqtt_state_topic__ = "mqtt_state_topic"
        self.__c_mqtt_availability_topic__ = "mqtt_availability_topic"
        self.__c_mqtt_will_topic__ = "will_topic"
        self.__c_mqtt_will_payload__ = "will_payload"
        self.__c_mqtt_birth_topic__ = "birth_topic"
        self.__c_mqtt_birth_payload__ = "birth_payload"
        self.__c_mqtt_alarm_triggered_topic__ = "qolsys_alarm_triggered_topic"
        self.__c_mqtt_alarm_pending_topic__ = "qolsys_alarm_pending_topic"

        # populate some variables we'll need to use throughout our app
        self.mqtt_namespace = self.get_arg(name=self.__c_mqtt_namespace__, arr=self.args, default="")
        # self.mqtt_namespace = self.args[self.__c_mqtt_namespace__] if self.__c_mqtt_namespace__ in self.args else ""
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
        self.qolsys_arm_away_always_instant = self.args[self.__c_qolsys_arm_away_always_instant__] if self.__c_qolsys_arm_away_always_instant__ in self.args else False
        self.homeassistant_mqtt_discovery_topic = self.fix_topic_name(self.get_arg(self.__c_homeassistant_mqtt_discovery_topic__, self.args, "homeassistant/"))
        self.mqtt_state_topic = self.fix_topic_name(self.get_arg(self.__c_mqtt_state_topic__, self.args, "mqtt-states/"))
        self.mqtt_availability_topic = self.fix_topic_name(self.get_arg(self.__c_mqtt_availability_topic__, self.args, "mqtt-availability/"))
        self.mqtt_plugin_config = self.get_plugin_config(namespace=self.mqtt_namespace)
        self.mqtt_will_topic = self.get_arg(name=self.__c_mqtt_will_topic__, arr=self.mqtt_plugin_config)
        self.mqtt_will_payload = self.get_arg(name=self.__c_mqtt_will_payload__, arr=self.mqtt_plugin_config)
        self.mqtt_birth_topic = self.get_arg(name=self.__c_mqtt_birth_topic__, arr=self.mqtt_plugin_config)
        self.mqtt_birth_payload = self.get_arg(name=self.__c_mqtt_birth_payload__, arr=self.mqtt_plugin_config)
        self.qolsys_alarm_triggered_topic = self.args[self.__c_mqtt_alarm_triggered_topic__] if self.__c_mqtt_alarm_triggered_topic__ in self.args else "qolsys/alarm/triggered"
        self.qolsys_alarm_pending_topic = self.args[self.__c_mqtt_alarm_pending_topic__] if self.__c_mqtt_alarm_pending_topic__ in self.args else "qolsys/alarm/pending"
        

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

        # Pending events come as ARMING / ENTRY_DELAY events... no need for a separate listener
        # self.log("listner for pending topic: %s", self.qolsys_pending_topic, level="INFO")
        # mqtt_sub.listen(mqtt_sub.mqtt_alarm_pending_event_received, self.qolsys_alarm_pending_topic)

        self.log("listner for triggered (ALARM) topic: %s", self.qolsys_alarm_triggered_topic, level="INFO")
        mqtt_sub.listen(mqtt_sub.mqtt_alarm_triggered_event_received, self.qolsys_alarm_triggered_topic)


        # Populate the zones and partitions with an INFO call
        info_payload = {"event":"INFO", "token":self.qolsys_token}
        self.call_service("mqtt/publish", namespace=self.mqtt_namespace, topic=self.request_topic, payload=json.dumps(info_payload))

        # config = self.get_plugin_config(namespace=self.mqtt_namespace)
        # self.log(config)

    def terminate(self):
        try:
            self.qolsys.close_socket()
            self.log("Socket closed")
        except:
            self.log("Error closing socket: %s", sys.exc_info(), level="ERROR")

        try:
            for zone in self.zones:
                # self.call_service("mqtt/publish", topic=self.zones[zone].config_topic, namespace=self.mqtt_namespace)
                self.call_service("mqtt/publish", namespace=self.mqtt_namespace, topic=self.zones[zone].availability_topic, payload=self.zones[zone].payload_not_available, retain=True)
            self.log("Zones removed")
        except:
            self.log("Error publishing empty zone: %s, %s", zone, sys.exc_info(), level="ERROR")

        try:
            for part in self.partitions:
                #self.call_service("mqtt/publish", topic=self.partitions[part].alarm_config_topic, namespace=self.mqtt_namespace)
                self.call_service("mqtt/publish", namespace=self.mqtt_namespace, topic=self.partitions[part].availability_topic, payload=self.partitions[part].payload_not_available, retain=True)
            self.log("Partitions set to unavailable")
        except:
            self.log("Error publishing offlining partition: %s, %s", part, sys.exc_info(), level="ERROR")

        self.log("Terminated")

    def qolsys_data_received(self, data:dict):
        ''' This is where any json data coming from the qolsys panel will be sent.
        In this case I have the data being published to a mqtt topic, but you can do what you want.
        
            Parameters:
                data: json object containing the output from the qolsys panel'''

        topic = "" #self.event_parent_topic
        jdata = json.loads(data)
        event_type = jdata["event"]

        if event_type == "ERROR":
            self.log("ERROR event: %s", data, level="ERROR")
        if event_type == "INFO":
            topic = self.qolsys_info_topic

        elif event_type == "ZONE_EVENT":
            zone_event_type = jdata["zone_event_type"]
            # Two types of zone events: ZONE_UPDATE, ZONE_ACTIVE
            # zone_event_type is unused for now
            topic = self.qolsys_zone_event_topic
            # if zone_event_type == "ZONE_UDPATE":
            #     topic = self.qolsys_zone_update_topic

        elif event_type == "ARMING":
            arming_type = jdata["arming_type"]
            # Three types of arming: ARM_STAY, EXIT_DELAY, DISARM
            topic = self.qolsys_arming_event_topic

        elif event_type == "ALARM":
            # The alarm is actually triggered
            topic = self.qolsys_alarm_triggered_topic

        else:
            topic = "qolsys/unknown_events"

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