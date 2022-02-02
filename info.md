# Volkswagen We Connect ID

This integration is only for the 'ID' cars from Volkswagen.

## Automation Examples

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


## Lovelace Examples
![image](https://user-images.githubusercontent.com/15835274/152117284-f0f6cd6e-02aa-4745-bc8d-906b8da781e6.png)

This example is by Puch-TDI (https://github.com/Puch-tdi)

```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: sensor.volkswagen_id_id_4_pro_performance_range
        name: ID4 Actieradius
        icon: mdi:speedometer
      - entity: binary_sensor.volkswagen_id_id_4_pro_performance_plug_connection_state
        name: Connected
      - entity: sensor.volkswagen_id_id_4_pro_performance_charge_rate
        name: Laadsnelheid Km/H
      - entity: sensor.volkswagen_id_id_4_pro_performance_remaining_charging_time
        name: Resterende laadtijd
        icon: mdi:clock-end
    title: Batterij info
    header:
      type: picture
      image: /local/id4-4.jpg
      tap_action:
        action: none
      hold_action:
        action: none
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.volkswagen_id_id_4_pro_performance_state_of_charge
        min: 0
        max: 100
        name: Accu status
        unit: '%'
        severity:
          green: 60
          yellow: 40
          red: 20
      - type: gauge
        entity: sensor.volkswagen_id_id_4_pro_performance_charge_power
        min: 0
        max: 125
        name: Laadsnelheid
        severity:
          green: 0
          yellow: 80
          red: 110
        unit: kW/H
        needle: true
    header:
```

```yaml
type: entities
entities:
  - entity: button.volkswagen_id_id_4_pro_performance_start_climate
    name: Climatisering aan/uit
    secondary_info: last-updated
  - entity: binary_sensor.volkswagen_id_id_4_pro_performance_rear_window_heating_state
    name: Achterruit verwarming
    icon: mdi:thermometer-lines
  - entity: >-
      binary_sensor.volkswagen_id_id_4_pro_performance_front_window_heating_state
    name: Voorruit verwarming
    icon: mdi:thermometer-chevron-up
  - entity: binary_sensor.volkswagen_id_id_4_pro_performance_zone_front_left_enabled
    name: Zone linksvoor
    icon: mdi:thermometer-low
  - entity: binary_sensor.volkswagen_id_id_4_pro_performance_zone_front_right_enabled
    icon: mdi:thermometer-low
    name: Zone rechtsvoor
  - entity: sensor.volkswagen_id_id_4_pro_performance_climatisation_state
    name: Climatisering status
    icon: mdi:air-conditioner
  - entity: sensor.volkswagen_id_id_4_pro_performance_remaining_climatisation_time
    icon: mdi:air-conditioner
    name: Resterende tijd clima
  - entity: sensor.volkswagen_id_id_4_pro_performance_target_temperature_c
    name: Ingestelde temperatuur
title: Climatisering
state_color: true
header:
  type: picture
  image: /local/id4-11.jpg
  tap_action:
    action: none
  hold_action:
    action: none
show_header_toggle: false
```

