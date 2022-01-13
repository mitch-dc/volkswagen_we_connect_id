# here_travel_time

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![License][license-shield]](LICENSE.md)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

[![Community Forum][forum-shield]][forum]

_Volkswagen We Connect ID sensor provides statistics from the Volkswagen ID Api thru [WeConnect-python lib](https://pypi.org/project/weconnect/)._

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show information from your Volkswagen ID car.

![example][exampleimg]

## Installation

### HACS

TODO: NOT AVAILABLE IN HACS YET

The easiest way to add this to your Homeassistant installation is using [HACS](https://custom-components.github.io/hacs/) and add this repository as a custom repository. And then follow the instructions under [Configuration](#configuration) below.

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `volkswagen_we_connect_id`.
4. Download _all_ the files from the `custom_components/volkswagen_we_connect_id/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Follow the instructions under [Configuration](#configuration) below.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/volkswagen_we_connect_id/__init__.py
custom_components/volkswagen_we_connect_id/manifest.json
custom_components/volkswagen_we_connect_id/sensor.py
.. etc
```

##  Configuration 

It's important that you first use the app, connect the app to the car and use it at least once. 
After that enable the integration on the integration page in Home Assistant with your e-mail and password that you use to login into the app. Wait a couple of seconds and 1 device (the car) with entities will show up. 

## Examples

My car is called Komo, and you will see that name in the examples. 
Replace the entities with the corresponding entities from your car.

Start warming up the cabin when it's freezing outside
```yaml
- alias: Car - Start preheating the cabin when it's freezing
  id: 4008ba82-bb35-4b2f-85b3-96dca152efd1 # Make this unique
  trigger:
    - platform: time
      at:
        - "07:00:00"
  condition:
    condition: numeric_state
    entity_id: weather.torentje
    attribute: temperature
    below: 1
  action:
  - service: volkswagen_we_connect_id.volkswagen_id_set_climatisation
    data:
      vin: WVGZZZE2ZMP4201337
      start_stop: start
      target_temp: 20
```

_My advice is to create a seperate automation for when the car actually starts heating up, the VW api is really slow and not really bullit proof._

Send messsage when car is heating up:
```yaml
automation:
- alias: Car - Notification when car started to heat up the cabin
  id: 919b5fbf-b1c7-41ec-a31f-3c9a14785bf0 # Make this unique
  trigger:
    - platform: state
      entity_id: sensor.volkswagen_id_komo_climatisation_state # Change entities
      to: "heating"
  action:
    - service: notify.mobile_app_mitchells_ifoon_app # Change entities
      data:
        message: "🔥 Komo is heating up the cabin to {{states.sensor.volkswagen_id_komo_target_temperature.state}}°C. It's done at {{ (now()|as_timestamp + (float(states('sensor.volkswagen_id_komo_remaining_climatisation_time')) * 60 ))|timestamp_custom('%H:%M', True) }}." # Change entities or change the message
        data:
          url: "/lovelace-car/car"
          push:
            thread-id: "car-group"
```

Send messsage when car is done charging:
```yaml
- alias: Car - Notification when car is done charging
  id: 22a8347c-4001-4795-a3de-71a89a428806 # Make this unique
  trigger:
    - platform: template
      value_template: "{{ states.sensor.volkswagen_id_komo_state_of_charge.state == states.sensor.volkswagen_id_komo_target_state_of_charge.state }}" # Change entities
  action:
    - service: notify.mobile_app_mitchells_ifoon_app # Change entities
      data:
        message: "🔋 Komo is done charging, current range is now {{states.sensor.volkswagen_id_komo_range.state}}km." # Change entities
        data:
          url: "/lovelace-car/car"
          push:
            thread-id: "car-group"
```

Send messsage when car has an error while charging:
```yaml
- alias: Car - Notification when car errored
  id: 791366e0-df10-465a-8706-30017d08ea91 # Make this unique
  trigger:
    - platform: state
      entity_id: sensor.volkswagen_id_komo_charging_state # Change entities
      from: "charging"
      to: "error"
  action:
    - service: notify.mobile_app_mitchells_ifoon_app # Change entities
      data:
        message: "🚨 Komo has an error while charging with {{states.sensor.volkswagen_id_komo_range.state}}km range." # Change entities
        data:
          url: "/lovelace-car/car"
          push:
            thread-id: "car-group"
```

Send messsage when car started charging:
```yaml
- alias: Car - Notification when car started charging
  id: dadf86c7-fd05-4aff-9891-e3d9f1eaf4dc # Make this unique
  trigger:
    - platform: state
      entity_id: sensor.volkswagen_id_komo_charging_state # Change entities
      to: "charging"
  action:
    - service: notify.mobile_app_mitchells_ifoon_app # Change entities
      data:
        message: "⚡ Komo started charging. It's done at {{ (now()|as_timestamp + (float(states('sensor.volkswagen_id_komo_remaining_charging_time')) * 60 ))|timestamp_custom('%H:%M', True) }} and will have {{states.sensor.volkswagen_id_komo_target_state_of_charge.state}}% battery." # Change entities
        data:
          url: "/lovelace-car/car"
          push:
            thread-id: "car-group"
```

