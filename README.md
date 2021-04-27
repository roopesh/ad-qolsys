
# ad-qolsys

AppDaemon app for Qolsys IQ Panel 2 _for Home Assistant_.  Only tested using the HA add-on AppDaemon.  Inspired by <https://community.home-assistant.io/t/qolsys-iq-panel-2-and-3rd-party-integration>

Fully self-contained AppDaemon app.  If you have HA MQTT Discovery turned on, you should end up with binary sensors for each `Door_Window` zone on the Qolsys panel. There are more zone types which I don’t own so I have not handled them in anyway.

You’ll also have an alarm_control_panel for each partition.  If you use the alarm panel component in HA, you don't have to worry about sending commands to the panel.  It'll all be auto-magiced with MQTT discovery.

Utilizes the MQTT plugin's `will_topic` to detect if AppDaemon is offline.  In order for this to work, MQTT plugin's `will_topic` and `birth_topic` _*must*_ be the same.  If they are not the same, AppDaemon's availability will be ignored and the `alarm_control_panel` and any `binary_sensor`'s statuses can be out of sync with reality during/after restarts.

Arguments in apps.yaml:

```yaml
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
# qolsys_disarm_code: (Required - if you want to disarm the alarm)
# qolsys_confirm_disarm_code: True/False (Optional) Require the code for disarming; defaults to False
# qolsys_confirm_arm_code: True/False (Optional) Require the code for arming; defaults to False
# qolsys_arm_away_always_instant: True/False (Optional) Set to true if all Arm Away commands should be instant; defaults to False
# homeassistant_mqtt_discovery_topic: homeassistant/ (Optional) The topic Home Assistant is using for MQTT Discovery (homeassistant/ is the default in HA and here)
# mqtt_state_topic: mqtt-states (Optional) The topic to publish state updates to for the alarm_control_panel and binary_sensor (default: mqtt-states)
# mqtt_availability_topic: mqtt-availability (Optional) The topic to publish availability events to for the alarm_control_panel and binary_sensor (default: mqtt-availability)
```

You’ll need you appdaemon's apps.yaml to include an app with this module and class:

```yaml
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
  qolsys_disarm_code: 4567 # Optional - Required if you want to disarm the panel
  qolsys_confirm_arm_code: False # Optional
  qolsys_confirm_disarm_code: False # Optional
  qolsys_arm_away_always_instant: False # Optional
```

As far MQTT is concerned, I had to figure out how to enable MQTT inside AppDaemon. In case you’re new to AppDaemon and have the same questions, I had to put this in my appdaemon.yaml:

```yaml
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

I’m by no means an MQTT or AppDaemon expert, so feel free to peruse the documentation for any MQTT configuration help you need <https://appdaemon.readthedocs.io/en/latest/MQTT_API_REFERENCE.html>

You can send commands to the Qolsys panel on the `request_topic` in the config (or `qolsys/requests` if not specified).  There are four commands:

```json
# Request the INFO to be published
{"event":"INFO", "token":"blah"}

# Arm stay:
{"event":"ARM", "arm_type":"stay", "partition_id": 0, "token":"blah"}

# Arm away
{"event":"ARM", "arm_type":"away", "partition_id": 0, "token":"blah"}

# (Variant) Arm away - Instant
{"event":"ARM", "arm_type":"away", "partition_id": 0, "token":"blah", "instant": true}

# Disarm
{"event":"DISARM", "usercode":0000, "token":"blah"}
```

Known issues:

- When the app reloads, sometimes it doesn’t reconnect to the socket and it just hangs the entire app. The only way I’ve been able to recover is to restart AppDaemon. If anyone has a way to detect and fix this, let me know or issue a pull request.

## I hope this works for everyone! Hit me up with feedback
