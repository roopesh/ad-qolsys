# ad-qolsys
AppDaemon app for Qolsys IQ Panel 2 _for Home Assistant_.  Only tested using the HA add-on AppDaemon.  Inspired by https://community.home-assistant.io/t/qolsys-iq-panel-2-and-3rd-party-integration

Fully self-contained AppDaemon app.  If you have HA MQTT Discovery turned on, you should end up with binary sensors for each `Door_Window` zone on the Qolsys panel. There are more zone types which I don’t own so I have not handled them in anyway.

You’ll also have an `alarm_control_panel` device in HA for each partition in your Qolsys panel.

Arguments in apps.yaml:
```
# mqtt_namespace: (optional) namespace for mqtt defined in appdaemon.yaml; defaults to ""
# qolsys_host: (Required) IP address or hostname for the qolsys panel
# qolsys_port: (Optional) Port on the qolsys panel to connect to; will default to 12345
# qolsys_token: (Required) Token from the qolsys panel
# request_topic: (Optional) The topic to listen to send commands to the qolsys panel; defaults to qolsys/requests
# qolsys_timeout: (Optional) The timeout (in seconds) to wait for any activity to/from the qolsys panel before disconnecting; defaults to 86400
# qolsys_info_topic: (Optional) The topic to publish qolsys INFO events to; defaults to qolsys/info
# qolsys_zone_event_topic: (Optional) The topic to publish ZONE_EVENT events to; defaults to qolsys/zone_event
# qolsys_alarming_event_topic: (Optional) The topic to publish ARMING events to; defaults to qolsys/arming
# qolsys_disarming_event_topic: (Optional) The topic to publish DISARMING events to; defaults to qolsys/disarming
# qolsys_alarm_status_topic: (Optional) The topic to publish alarm status for the alarm_control_panel; defaults to qolsys/alarm/status
```
You’ll need you appdaemon's apps.yaml to include an app with this module and class:
```
qolsys_panel:
  module: qolsys_client
  class: QolsysClient
  mqtt_namespace: mqtt <see below for my config>
  qolsys_host: <your IP here>
  qolsys_token: <your token here>
  qolsys_port: 12345 # Optional
  request_topic: qolsys/requests # Optional
  qolsys_info_topic: qolsys/panel/info # Optional
  qolsys_zone_update_topic: qolsys/panel/zone_update # Optional
  qolsys_zone_event_topic: qolsys/panel/zone_event # Optional
  qolsys_alarming_event_topic: qolsys/panel/alarming # Optional
  qolsys_disarming_event_topic: qolsys/panel/disarm # Optional
  qolsys_alarm_status_topic: qolsys/alarm/status # Optional
```
As far MQTT is concerned, I had to figure out how to enable MQTT inside AppDaemon. In case you’re new to AppDaemon and have the same questions, I had to put this in my appdaemon.yaml:
```
appdaemon:
  latitude: # existing
  longitude: # existing
  elevation: # existing
  time_zone: # your timezone America/Los_Angeles
  # HASS plugin is enabled by default if you're using the add-on
  plugins:
    HASS:
      type: hass
    # I added on the MQTT plugin
    MQTT:
      type: mqtt
      namespace: mqtt #you will need this namespace name in your apps.yaml
      # The IP Address or hostname of your MQTT broker.  
      client_host: 192.168.x.y
      client_port: 1883
```
I’m by no means an MQTT or AppDaemon expert, so feel free to peruse the documentation for any MQTT configuration help you need https://appdaemon.readthedocs.io/en/latest/MQTT_API_REFERENCE.html.

You can send commands to the Qolsys panel on the `request_topic` in the config (or `qolsys/requests` if not specified).  There are four commands:
```
# Request the INFO to be published
{"event":"INFO", "token":"blah"}

# Arm stay:
{"event":"ARM", "arm_type":"stay", "partition_id": 0, "token":"blah"}

# Arm away
{"event":"ARM", "arm_type":"away", "partition_id": 0, "token":"blah"}

# Disarm
{"event":"DISARM", "usercode":"0000", "token":"blah"}
```
Known issues:

- When the app reloads, sometimes it doesn’t reconnect to the socket and it just hangs the entire app. The only way I’ve been able to recover is to restart AppDaemon. If anyone has a way to detect and fix this, let me know or issue a pull request.

~- I’m not yet processing arming/disarming events. The requests will work 💯, but the partition doesn’t get updated with the status. I put in another INFO request so the partition sensor will update but it’s a bit hacky for now. If you’re listening to the topics or watching logs, you’ll see a bunch of noise associated with this hack.~

~- Partition status being tracked as a `binary_sensor` instead of `alarm_control_panel`.~
- MQTT Discovery is being published to `homeassistant/binary_sensor`. I’ll make this a config in the future. This is the default MQTT Discovery topic so I think most people will be fine.

### I hope this works for everyone! Hit me up with feedback.
