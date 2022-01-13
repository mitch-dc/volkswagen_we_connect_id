"""Platform for sensor integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import cast

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from . import VolkswagenIDBaseEntity
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    LENGTH_KILOMETERS,
    PERCENTAGE,
    POWER_KILO_WATT,
    SPEED_KILOMETERS_PER_HOUR,
    TEMP_CELSIUS,
    TIME_MINUTES,
)
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CLIMASTATUS_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key="climatisationState", name="Climatisation State"),
    SensorEntityDescription(
        key="remainingClimatisationTime_min",
        name="Remaining Climatisation Time",
        native_unit_of_measurement=TIME_MINUTES,
    ),
)

CLIMASETTINGS_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="targetTemperature_C",
        name="Target Temperature",
        device_class=DEVICE_CLASS_TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
    ),
)

CHARGESTATUS_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="chargingState",
        name="Charging State",
        icon="mdi:ev-station",
    ),
    SensorEntityDescription(
        key="remainingChargingTimeToComplete_min",
        name="Remaining Charging Time",
        native_unit_of_measurement=TIME_MINUTES,
    ),
    SensorEntityDescription(
        key="chargePower_kW",
        name="Charge Power",
        native_unit_of_measurement=POWER_KILO_WATT,
        device_class=DEVICE_CLASS_POWER,
    ),
    SensorEntityDescription(
        key="chargeRate_kmph",
        name="Charge Rate",
        native_unit_of_measurement=SPEED_KILOMETERS_PER_HOUR,
        device_class=DEVICE_CLASS_POWER,
    ),
)

CHARGESETTINGS_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(key="maxChargeCurrentAC", name="Charge Current AC"),
    SensorEntityDescription(
        key="targetSOC_pct",
        name="Target State of Charge",
        device_class=DEVICE_CLASS_BATTERY,
        native_unit_of_measurement=PERCENTAGE,
    ),
)

BATTERYSTATUS_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="currentSOC_pct",
        name="State of Charge",
        device_class=DEVICE_CLASS_BATTERY,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        name="Range",
        key="cruisingRangeElectric_km",
        native_unit_of_measurement=LENGTH_KILOMETERS,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    weConnect = hass.data[DOMAIN][config_entry.entry_id]
    await hass.async_add_executor_job(weConnect.update)

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        await hass.async_add_executor_job(weConnect.update)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="volkswagen_we_connect_id_sensors",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=15),
    )

    entities: list[VolkswagenIDSensor] = []
    for vin, vehicle in weConnect.vehicles.items():
        for sensor in CLIMASTATUS_SENSORS:
            entities.append(
                VolkswagenIDSensor(
                    vehicle,
                    sensor,
                    vehicle.domains["climatisation"]["climatisationStatus"],
                    weConnect,
                    coordinator,
                )
            )
        for sensor in CLIMASETTINGS_SENSORS:
            entities.append(
                VolkswagenIDSensor(
                    vehicle,
                    sensor,
                    vehicle.domains["climatisation"]["climatisationSettings"],
                    weConnect,
                    coordinator,
                )
            )
        for sensor in CHARGESTATUS_SENSORS:
            entities.append(
                VolkswagenIDSensor(
                    vehicle,
                    sensor,
                    vehicle.domains["charging"]["chargingStatus"],
                    weConnect,
                    coordinator,
                )
            )
        for sensor in CHARGESETTINGS_SENSORS:
            entities.append(
                VolkswagenIDSensor(
                    vehicle,
                    sensor,
                    vehicle.domains["charging"]["chargingSettings"],
                    weConnect,
                    coordinator,
                )
            )
        for sensor in BATTERYSTATUS_SENSORS:
            entities.append(
                VolkswagenIDSensor(
                    vehicle,
                    sensor,
                    vehicle.domains["charging"]["batteryStatus"],
                    weConnect,
                    coordinator,
                )
            )
    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, SensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: SensorEntityDescription

    def __init__(self, vehicle, description, data, we_connect, coordinator) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(vehicle, data, we_connect, coordinator)
        self.entity_description = description
        self._coordinator = coordinator
        self._attr_name = f"Volkswagen ID {vehicle.nickname} {description.name}"
        self._attr_unique_id = f"{vehicle.vin}-{description.key}"
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        state = getattr(self._data, self.entity_description.key).value

        if hasattr(state, "value"):
            state = state.value

        return cast(StateType, state)
