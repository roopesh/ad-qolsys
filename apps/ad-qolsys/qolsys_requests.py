import sys
import time
import qolsys_socket
import appdaemon.plugins.mqtt.mqttapi as mqtt
import json
import door_window
import partition
import re


class MQTTSubscriber:
    def __init__(self, app: mqtt, qolsys: qolsys_socket.qolsys):
        self.qolsys = qolsys
        self.app = app
        self._arming_types = ["away", "stay", "disarm"]

    def listen(self, cb:callable, topic):
        #self.app.log("MQTT Subscriber: %s : %s : %s", self.app.mqtt_broker, self.app.mqtt_port, topic, level="DEBUG")
        self.app.mqtt_subscribe(topic, namespace=self.app.mqtt_namespace)
        #self.app.log("listener for event: %s", topic, level="INFO")
        self.app.listen_event(cb, event="MQTT_MESSAGE", topic=topic, namespace=self.app.mqtt_namespace)

    def mqtt_zone_update_event_received(self, event_name, data, kwargs):
        self.app.log("Got zone Update event: %s", data, level="DEBUG")
        self.app.log("event_name: %s", event_name, level="DEBUG")
        self.app.log("data: %s", data, level="DEBUG")
        self.app.log("kwargs: %s", kwargs, level="DEBUG")
        payload_json = self.__get_mqtt_payload_json__(data)
        zone = payload_json["zone"]
        zoneid = zone["zone_id"]
        state = zone["status"]
        self.app.log("Zones: %s", self.app.zones, level="DEBUG")
        this_zone = self.app.zones[zoneid]
        this_zone.state = state
        self.app.update_zone(zoneid, this_zone)
        self.app.log("Zones: %s", self.app.zones, level="DEBUG")
        self.app.log("Publishing to: %s, Payload: %s", this_zone.state_topic, state, level="INFO")
        self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_zone.state_topic, payload=state)

    def mqtt_arming_event_received(self, event_name, data, kwargs):
        self.app.log("Got arming event: %s", data, level="INFO")
        self.app.log("event_name: %s", event_name, level="INFO")
        self.app.log("data: %s", data, level="INFO")
        self.app.log("kwargs: %s", kwargs, level="INFO")
        payload_json = self.__get_mqtt_payload_json__(data)
        partition_id = payload_json["partition_id"]
        arming_type = payload_json["arming_type"]
        this_partition = self.app.partitions[partition_id]
        this_partition.status = arming_type
        self.app.update_zone(partition_id, this_partition)
        self.app.log("Partitions: %s", self.app.partitions, level="INFO")
        self.app.log("Publishing to: %s, Payload: %s", this_partition.alarm_panel_state_topic, this_partition.status, level="INFO")
        self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.alarm_panel_state_topic, payload=this_partition.status)

    def mqtt_alarm_triggered_event_received(self, event_name, data, kwargs):
        self.app.log("Got ALARM event: %s", data, level="INFO")
        self.app.log("event_name: %s", event_name, level="INFO")
        self.app.log("data: %s", data, level="INFO")
        self.app.log("kwargs: %s", kwargs, level="INFO")
        payload_json = self.__get_mqtt_payload_json__(data)
        partition_id = payload_json["partition_id"]
        alarm_type = payload_json["alarm_type"]
        this_partition = self.app.partitions[partition_id]
        this_partition.status = payload_json["event"] # This should be "ALARM"
        self.app.update_zone(partition_id, this_partition)
        self.app.log("Partitions: %s", self.app.partitions, level="INFO")
        self.app.log("Publishing to: %s, Payload: %s", this_partition.alarm_panel_state_topic, this_partition.status, level="INFO")
        self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.alarm_panel_state_topic, payload=this_partition.status)


    def mqtt_zone_event_event_received(self, event_name, data, kwargs):
        self.app.log("Got zone event: %s", data, level="DEBUG")
        self.mqtt_zone_update_event_received(event_name, data, kwargs)

    def mqtt_info_event_received(self, event_name, data, kwargs):
        self.app.log("Got zone info event: %s", data, level="DEBUG")
        # self.app.log("event_name: %s", event_name, level="INFO")
        self.app.log("data: %s", data, level="DEBUG")
        self.app.log("topic: %s", data["topic"], level="DEBUG")
        self.app.log("kwargs: %s", kwargs, level="DEBUG")
        payload_json = self.__get_mqtt_payload_json__(data)
        self.app.log("INFO: %s", payload_json, level="DEBUG")

        # loop through the door_window zones
        for part in payload_json["partition_list"]:
            # Save the partition
            partition_id = part["partition_id"]
            partition_name = part["name"]
            partition_status = part["status"]
            # self.app.log(self.app.mqtt_plugin_config)
            homeassistant_mqtt_discovery_topic = self.app.homeassistant_mqtt_discovery_topic
            this_partition = partition.partition(
                p_id=partition_id, 
                name=partition_name, 
                status=partition_status, 
                code=self.app.qolsys_disarm_code, 
                confirm_code_arm=self.app.qolsys_confirm_arm_code, 
                confirm_code_disarm=self.app.qolsys_confirm_disarm_code, 
                token=self.app.qolsys_token,
                will_topic = self.app.mqtt_will_topic,
                will_payload = self.app.mqtt_will_topic,
                birth_topic = self.app.mqtt_birth_topic,
                birth_payload = self.app.mqtt_birth_payload,
                homeassistant_mqtt_discovery_topic = homeassistant_mqtt_discovery_topic,
                mqtt_state_topic = self.app.mqtt_state_topic,
                mqtt_availability_topic = self.app.mqtt_availability_topic
            )
            self.app.update_partition(partition_id, this_partition)
            # self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.config_topic, payload=json.dumps(this_partition.config_payload()))
            # self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.state_topic, payload=this_partition.status)
            # self.app.log("topic: %s, payload: %s", this_partition.alarm_panel_config_topic, this_partition.alarm_config_payload())
            self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.alarm_panel_config_topic, retain=True, payload=json.dumps(this_partition.alarm_config_payload()))
            self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.alarm_panel_state_topic, payload=this_partition.status)
            self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_partition.availability_topic, payload=this_partition.payload_available)


            # self.app.partitions[partition_id] = partition_name

            for zone in part["zone_list"]:
                # Get the variables
                zoneid = zone["zone_id"]
                friendly_name = zone["name"]
                state = zone["status"]
                zone_type = zone["type"]
                zone_unique_id = zone["id"]

                # Add this zone to this partition
                this_partition.add_zone(zoneid)
                
                if zone_type:
                    this_zone = door_window.door_window(
                        zoneid = zoneid,
                        name = friendly_name,
                        state = state,
                        partition_id = partition_id,
                        device_class = self.__device_class_mapping__(zone_type),
                        will_topic = self.app.mqtt_will_topic,
                        will_payload = self.app.mqtt_will_topic,
                        birth_topic = self.app.mqtt_birth_topic,
                        birth_payload = self.app.mqtt_birth_payload,
                        homeassistant_mqtt_discovery_topic = homeassistant_mqtt_discovery_topic,
                        mqtt_state_topic = self.app.mqtt_state_topic,
                        mqtt_availability_topic = self.app.mqtt_availability_topic,
                        unique_id = zone_unique_id
                    )
                    #self.app.zones[zoneid] = this_zone
                    

                    self.app.update_zone(zoneid, this_zone)
                    self.app.log("Publishing zone: %s", json.dumps(this_zone.config_payload()), level="DEBUG")
                    self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_zone.config_topic, retain=True, payload=json.dumps(this_zone.config_payload()))
                    self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_zone.state_topic, payload=this_zone.state)
                    self.app.call_service("mqtt/publish", namespace=self.app.mqtt_namespace, topic=this_zone.availability_topic, payload=this_zone.payload_available)

        # done creating the zones
        # self.app.log("Partitions: %s", self.app.partitions, level="INFO")
        #self.app.log("Zones: %s", self.app.zones, level="DEBUG")
        # for zone in self.app.zones:
        #     self.app.log("zone: %s", zone, level="DEBUG")

    def __device_class_mapping__(self, device_class):
        mapping = {
            "Door_Window": "door",
            "SmokeDetector": "smoke",
            "GlassBreak": "safety",
            "Motion": "motion",
            "Water":"moisture",
            "CODetector": "gas"
            }
        if device_class in mapping:
            return mapping[device_class]
        else:
            return ""
    def __get_mqtt_payload_json__(self, data):
        self.app.log("data: %s", data, level="DEBUG")
        payload_json = {}
        try:
            payload = data["payload"]
            self.app.log("payload: %s", payload, level="DEBUG")
            try:
                if json.loads(payload):
                    payload_json = json.loads(payload)
                    self.app.log("payload_json: %s", payload_json, level="DEBUG")
            except:
                self.app.log("Error converting payload to json: %s", payload)
        except:
            self.app.log("Error getting payload from data: %s", data)
        return payload_json
        
    def mqtt_request_received(self, event_name, data, kwargs): 
        '''Runs when a MQTT event is received on the request topic
        
            Parameters:
                data: json object containing the request to send to the qolsys panel
            
            Expected JSON Message:
                Required:
                    event                   INFO, ARM, DISARM
                    token                   Qolsys IQ Panel token

                Optional
                    usercode                Required if disarming
                    partition_id            Required if arming or disarming.  0 is a good value if you don't know what to use
                    arm_type                Required if arming.  Options are "away" or "stay"
                    instant                 Optional during away arming.  Sets delay to 0.
                    delay                   Optional delay in seconds when arming away
                '''

        self.app.log("event_name: %s", event_name, level="DEBUG")
        self.app.log("kwargs: %s", kwargs, level="DEBUG")
        payload_json = self.__get_mqtt_payload_json__(data) # {}
        event_type = ""
        
        try:
            event_type = payload_json["event"]
            self.app.log("event: %s", event_type, level="INFO")
        except:
            self.app.log("Unable to find 'event': %s", payload_json, level="ERROR")

        if event_type != "":
            token = payload_json["token"] if "token" in payload_json else None
            usercode = payload_json["usercode"] if "usercode" in payload_json else None
            partition_id = payload_json["partition_id"] if "partition_id" in payload_json else None
            arm_type = payload_json["arm_type"] if "arm_type" in payload_json else None
            delay = payload_json["delay"] if "delay" in payload_json else -1
            
            instant = payload_json["instant"] if "instant" in payload_json else False
            if self.app.qolsys_arm_away_always_instant: instant = True
            
            self.app.log("event: %s, usercode: %s, partition_id: %s, arm_type: %s, instant: %s", event_type, usercode, partition_id, arm_type, instant, level="INFO")
            if token == None:
                #raise("Token required for anything you want to do")
                self.app.log("No token provided.  Token is required for anything you want to do with the Qolsys panel", level="ERROR")
            else:
                if event_type == "INFO":
                    self.__qolsys_status__(qolsys=self.qolsys, token=token)
                
                if event_type == "ARM":
                    if partition_id is None or arm_type is None:
                        self.app.log("arm_type and partition_id are required", level="ERROR")
                    else:                    
                        self.__qolsys_arm__(qolsys=self.qolsys, token=token, arming_type=arm_type, partition_id=partition_id, instant=instant, usercode=usercode, delay=delay)

                if event_type == "DISARM":
                    arm_type = "disarm"
                    if partition_id is None or arm_type is None or usercode is None:
                        self.app.log("arm_type, partition_id, and usercode are required", level="ERROR")
                    else:                    
                        self.__qolsys_arm__(qolsys=self.qolsys, token=token, arming_type="disarm", partition_id=partition_id, usercode=usercode)

    def __qolsys_arm__(self, qolsys, token:str, arming_type:str, partition_id:int, instant=False, usercode="", delay=-1):
        if not arming_type in self._arming_types:
            raise("Invalid arm command")

        arm_type = ""

        if arming_type.lower() == 'away':
            arm_type = "ARM_AWAY"
        elif arming_type.lower() == 'stay':
            arm_type = "ARM_STAY"
        elif arming_type.lower() == 'disarm':
            arm_type = "DISARM"
        else:
            raise("Invalid arm command")

        armString    = {
                            "partition_id": partition_id,
                            "action":       "ARMING",
                            "arming_type":  arm_type,
                            "version":      0,
                            "nonce":        "qolsys",
                            "source":       "C4",
                            "version_key":  1,
                            "source_key":   "C4",
                            "token":        token,
                            "usercode":     usercode
                        }

        if arming_type.lower() == "away" and instant:
            armString.update({"delay": 0})

        if arming_type.lower() == "away" and not instant and int(delay)>0:
            armString.update({"delay": delay})

        try:
            self.app.log("armString: %s", armString, level="INFO")
            qolsys.send_to_socket(armString)
        except socket.error:
            self.app.log("Could not send arm command to qolsys socket", level="ERROR")

    def __qolsys_status__(self, qolsys, token):
        statusString    = {
                            "nonce":        "qolsys",
                            "action":       "INFO",
                            "info_type":    "SUMMARY",
                            "version":      0,
                            "source":       "C4",
                            "token":        token,
                        }

        try:
            qolsys.send_to_socket(statusString)
        except:
            self.app.log('Could not send status request to qolsys socket', level="ERROR")

