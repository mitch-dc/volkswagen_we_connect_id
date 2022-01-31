"""Platform for sensor integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging

from weconnect import weconnect
from weconnect.elements.plug_status import PlugStatus
from weconnect.elements.window_heating_status import WindowHeatingStatus
from weconnect.elements.charging_settings import ChargingSettings

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import VolkswagenIDBaseEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class VolkswagenIdBinaryEntityDescription(BinarySensorEntityDescription):
    """Describes Volkswagen ID binary sensor entity."""

    local_address: str | None = None
    on_value: None = None


SENSORS: tuple[VolkswagenIdBinaryEntityDescription, ...] = (
    VolkswagenIdBinaryEntityDescription(
        key="climatisationWithoutExternalPower",
        name="Climatisation Without External Power",
        local_address="/climatisation/climatisationSettings/climatisationWithoutExternalPower",
    ),
    VolkswagenIdBinaryEntityDescription(
        key="climatizationAtUnlock",
        name="Climatisation At Unlock",
        local_address="/climatisation/climatisationSettings/climatizationAtUnlock",
    ),
    VolkswagenIdBinaryEntityDescription(
        key="zoneFrontLeftEnabled",
        name="Zone Front Left Enabled",
        local_address="/climatisation/climatisationSettings/zoneFrontLeftEnabled",
    ),
    VolkswagenIdBinaryEntityDescription(
        key="zoneFrontRightEnabled",
        name="Zone Front Right Enabled",
        local_address="/climatisation/climatisationSettings/zoneFrontRightEnabled",
    ),
    VolkswagenIdBinaryEntityDescription(
        key="windowHeatingEnabled",
        name="Window Heating Enabled",
        local_address="/climatisation/climatisationSettings/windowHeatingEnabled",
    ),
    VolkswagenIdBinaryEntityDescription(
        key="frontWindowHeatingState",
        name="Front Window Heating State",
        local_address="/climatisation/windowHeatingStatus/windows/front/windowHeatingState",
        on_value=WindowHeatingStatus.Window.WindowHeatingState.ON,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="rearWindowHeatingState",
        name="Rear Window Heating State",
        local_address="/climatisation/windowHeatingStatus/windows/rear/windowHeatingState",
        on_value=WindowHeatingStatus.Window.WindowHeatingState.ON,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="autoUnlockPlugWhenCharged",
        name="Auto Unlock Plug When Charged",
        local_address="/charging/chargingSettings/autoUnlockPlugWhenCharged",
        on_value=ChargingSettings.UnlockPlugState.ON,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="plugConnectionState",
        name="Plug Connection State",
        local_address="/charging/plugStatus/plugConnectionState",
        device_class=BinarySensorDeviceClass.PLUG,
        on_value=PlugStatus.PlugConnectionState.CONNECTED,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="plugLockState",
        name="Plug Lock State",
        local_address="/charging/plugStatus/plugLockState",
        device_class=BinarySensorDeviceClass.LOCK,
        on_value=PlugStatus.PlugLockState.LOCKED,
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
        update_interval=timedelta(seconds=30),
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


class VolkswagenIDSensor(VolkswagenIDBaseEntity, BinarySensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: VolkswagenIdBinaryEntityDescription

    def __init__(
        self,
        vehicle: weconnect.Vehicle,
        sensor: VolkswagenIdBinaryEntityDescription,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(vehicle, sensor, we_connect, coordinator)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"Volkswagen ID {vehicle.nickname} {sensor.name}"
        self._attr_unique_id = f"{vehicle.vin}-{sensor.key}"
        self._data = f"/vehicles/{vehicle.vin}/domains{sensor.local_address}"

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""

        state = self._we_connect.getByAddressString(self._data)

        while hasattr(state, "value"):
            state = state.value

        if type(state) is bool:
            return state

        return state == self.entity_description.on_value.value
