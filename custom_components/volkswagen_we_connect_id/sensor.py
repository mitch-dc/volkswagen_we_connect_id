"""Platform for sensor integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import cast

from weconnect import weconnect

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    LENGTH_KILOMETERS,
    PERCENTAGE,
    POWER_KILO_WATT,
    SPEED_KILOMETERS_PER_HOUR,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    TIME_MINUTES,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import VolkswagenIDBaseEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class VolkswagenIdEntityDescription(SensorEntityDescription):
    """Describes Volkswagen ID sensor entity."""

    local_address: str | None = None


SENSORS: tuple[VolkswagenIdEntityDescription, ...] = (
    VolkswagenIdEntityDescription(
        key="climatisationState",
        name="Climatisation State",
        local_address="/climatisation/climatisationStatus/climatisationState",
    ),
    VolkswagenIdEntityDescription(
        key="remainingClimatisationTime_min",
        name="Remaining Climatisation Time",
        native_unit_of_measurement=TIME_MINUTES,
        local_address="/climatisation/climatisationStatus/remainingClimatisationTime_min",
    ),
    VolkswagenIdEntityDescription(
        key="targetTemperature_C",
        name="Target Temperature C",
        device_class=DEVICE_CLASS_TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        local_address="/climatisation/climatisationSettings/targetTemperature_C",
    ),
    VolkswagenIdEntityDescription(
        key="targetTemperature_F",
        name="Target Temperature F",
        device_class=DEVICE_CLASS_TEMPERATURE,
        native_unit_of_measurement=TEMP_FAHRENHEIT,
        local_address="/climatisation/climatisationSettings/targetTemperature_F",
    ),
    VolkswagenIdEntityDescription(
        key="unitInCar",
        name="Unit In car",
        local_address="/climatisation/climatisationSettings/unitInCar",
    ),
    VolkswagenIdEntityDescription(
        key="chargingState",
        name="Charging State",
        icon="mdi:ev-station",
        local_address="/charging/chargingStatus/chargingState",
    ),
    VolkswagenIdEntityDescription(
        key="remainingChargingTimeToComplete_min",
        name="Remaining Charging Time",
        native_unit_of_measurement=TIME_MINUTES,
        local_address="/charging/chargingStatus/remainingChargingTimeToComplete_min",
    ),
    VolkswagenIdEntityDescription(
        key="chargeMode",
        name="Charging Mode",
        icon="mdi:ev-station",
        local_address="/charging/chargingStatus/chargeMode",
    ),
    VolkswagenIdEntityDescription(
        key="chargePower_kW",
        name="Charge Power",
        native_unit_of_measurement=POWER_KILO_WATT,
        device_class=DEVICE_CLASS_POWER,
        local_address="/charging/chargingStatus/chargePower_kW",
    ),
    VolkswagenIdEntityDescription(
        key="chargeRate_kmph",
        name="Charge Rate",
        native_unit_of_measurement=SPEED_KILOMETERS_PER_HOUR,
        device_class=DEVICE_CLASS_POWER,
        local_address="/charging/chargingStatus/chargeRate_kmph",
    ),
    VolkswagenIdEntityDescription(
        key="maxChargeCurrentAC",
        name="Charge Current AC",
        local_address="/charging/chargingSettings/maxChargeCurrentAC",
    ),
    VolkswagenIdEntityDescription(
        key="targetSOC_pct",
        name="Target State of Charge",
        device_class=DEVICE_CLASS_BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        local_address="/charging/chargingSettings/targetSOC_pct",
    ),
    VolkswagenIdEntityDescription(
        key="currentSOC_pct",
        name="State of Charge",
        device_class=DEVICE_CLASS_BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        local_address="/charging/batteryStatus/currentSOC_pct",
    ),
    VolkswagenIdEntityDescription(
        name="Range",
        key="cruisingRangeElectric_km",
        native_unit_of_measurement=LENGTH_KILOMETERS,
        local_address="/charging/batteryStatus/cruisingRangeElectric_km",
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    we_connect: weconnect.WeConnect
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    vehicles = hass.data[DOMAIN][config_entry.entry_id + "_vehicles"]

    async def async_update_data():
        await hass.async_add_executor_job(we_connect.update)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="volkswagen_we_connect_id_sensors",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=10),
    )

    entities: list[VolkswagenIDSensor] = []
    for vin, vehicle in vehicles.items():
        for sensor in SENSORS:
            entities.append(
                VolkswagenIDSensor(
                    vehicle,
                    sensor,
                    we_connect,
                    coordinator,
                )
            )
    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, SensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: VolkswagenIdEntityDescription

    def __init__(
        self,
        vehicle: weconnect.Vehicle,
        sensor: VolkswagenIdEntityDescription,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(vehicle, sensor, we_connect, coordinator)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"Volkswagen ID {vehicle.nickname} {sensor.name}"
        self._attr_unique_id = f"{vehicle.vin}-{sensor.key}"
        self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
        self._data = f"/vehicles/{vehicle.vin}{sensor.local_address}"

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        state = self._we_connect.getByAddressString(self._data)

        while hasattr(state, "value"):
            state = state.value

        return cast(StateType, state)
