"""Binary_sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from weconnect import weconnect
from weconnect.elements.plug_status import PlugStatus
from weconnect.elements.lights_status import LightsStatus
from weconnect.elements.window_heating_status import WindowHeatingStatus

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import VolkswagenIDBaseEntity, get_object_value
from .const import DOMAIN


@dataclass
class VolkswagenIdBinaryEntityDescription(BinarySensorEntityDescription):
    """Describes Volkswagen ID binary sensor entity."""

    value: Callable = lambda x, y: x
    on_value: object | None = None
    enabled: Callable = lambda x, y: x


SENSORS: tuple[VolkswagenIdBinaryEntityDescription, ...] = (
    VolkswagenIdBinaryEntityDescription(
        key="climatisationWithoutExternalPower",
        name="Climatisation Without External Power",
        value=lambda data: data["climatisation"][
            "climatisationSettings"
        ].climatisationWithoutExternalPower,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="climatizationAtUnlock",
        name="Climatisation At Unlock",
        value=lambda data: data["climatisation"][
            "climatisationSettings"
        ].climatizationAtUnlock,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="zoneFrontLeftEnabled",
        name="Zone Front Left Enabled",
        value=lambda data: data["climatisation"][
            "climatisationSettings"
        ].zoneFrontLeftEnabled,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="zoneFrontRightEnabled",
        name="Zone Front Right Enabled",
        value=lambda data: data["climatisation"][
            "climatisationSettings"
        ].zoneFrontRightEnabled,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="windowHeatingEnabled",
        name="Window Heating Enabled",
        value=lambda data: data["climatisation"][
            "climatisationSettings"
        ].windowHeatingEnabled,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="frontWindowHeatingState",
        name="Front Window Heating State",
        value=lambda data: data["climatisation"]["windowHeatingStatus"]
        .windows["front"]
        .windowHeatingState,
        on_value=WindowHeatingStatus.Window.WindowHeatingState.ON,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="rearWindowHeatingState",
        name="Rear Window Heating State",
        value=lambda data: data["climatisation"]["windowHeatingStatus"]
        .windows["rear"]
        .windowHeatingState,
        on_value=WindowHeatingStatus.Window.WindowHeatingState.ON,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="insufficientBatteryLevelWarning",
        name="Insufficient Battery Level Warning",
        value=lambda data: data["readiness"][
            "readinessStatus"
        ].connectionWarning.insufficientBatteryLevelWarning,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Car Is Online",
        key="isOnline",
        value=lambda data: data["readiness"][
            "readinessStatus"
        ].connectionState.isOnline,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Car Is Active",
        key="isActive",
        value=lambda data: data["readiness"][
            "readinessStatus"
        ].connectionState.isActive,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Lights Right",
        key="lightsRight",
        value=lambda data: data["vehicleLights"]["lightsStatus"].lights["right"].status,
        on_value=LightsStatus.Light.LightState.ON,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Lights Left",
        key="lightsLeft",
        value=lambda data: data["vehicleLights"]["lightsStatus"].lights["left"].status,
        on_value=LightsStatus.Light.LightState.ON,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    we_connect: weconnect.WeConnect
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities: list[VolkswagenIDSensor] = []

    for index, vehicle in enumerate(coordinator.data):
        for sensor in SENSORS:
            entities.append(VolkswagenIDSensor(sensor, we_connect, coordinator, index))
    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, BinarySensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: VolkswagenIdBinaryEntityDescription

    def __init__(
        self,
        sensor: VolkswagenIdBinaryEntityDescription,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(we_connect, coordinator, index)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"{self.data.nickname} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""
        try:
            state = self.entity_description.value(self.data.domains)
            if state.enabled and isinstance(state.value, bool):
                return state.value

            return False

        except KeyError:
            return None
