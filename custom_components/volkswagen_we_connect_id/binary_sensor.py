"""Binary_sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from carconnectivity import carconnectivity
from carconnectivity.lights import Lights
from carconnectivity_connectors.volkswagen.vehicle import VolkswagenElectricVehicle

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import DomainEntry, VolkswagenIDBaseEntity
from .const import DOMAIN


@dataclass
class VolkswagenIdBinaryEntityDescription(BinarySensorEntityDescription):
    """Describes Volkswagen ID binary sensor entity."""

    value: Callable[[VolkswagenElectricVehicle]] = lambda x, _: x
    on_value: object | None = None
    enabled: Callable[[VolkswagenElectricVehicle]] = lambda x, _: x


SENSORS: tuple[VolkswagenIdBinaryEntityDescription, ...] = (
    VolkswagenIdBinaryEntityDescription(
        key="climatisationWithoutExternalPower",
        name="Climatisation Without External Power",
        icon="mdi:fan",
        value=lambda data: data.climatization.settings.climatization_without_external_power,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="climatizationAtUnlock",
        name="Climatisation At Unlock",
        icon="mdi:fan",
        value=lambda data: data.climatization.settings.climatization_at_unlock,
    ),
    VolkswagenIdBinaryEntityDescription(
        key="windowHeatingEnabled",
        name="Window Heating Enabled",
        icon="mdi:car-defrost-front",
        value=lambda data: data.climatization.settings.window_heating,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Car Is Online",
        key="isOnline",
        value=lambda data: data.connection_state is VolkswagenElectricVehicle.ConnectionState.ONLINE,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Car Is Active",
        key="isActive",
        icon="mdi:car-side",
        value=lambda data: data.is_active,
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Lights Right",
        key="lightsRight",
        icon="mdi:car-light-dimmed",
        value=lambda data: data.lights.lights["right"].light_state,
        on_value=Lights.LightState.ON
    ),
    VolkswagenIdBinaryEntityDescription(
        name="Lights Left",
        key="lightsLeft",
        icon="mdi:car-light-dimmed",
        value=lambda data: data.lights.lights["left"].light_state,
        on_value=Lights.LightState.ON
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add sensors for passed config_entry in HA."""
    domain_entry: DomainEntry = hass.data[DOMAIN][config_entry.entry_id]
    car_connectivity = domain_entry.car_connectivity
    coordinator = domain_entry.coordinator

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities: list[VolkswagenIDSensor] = []

    for index, _ in enumerate(coordinator.data):
        for sensor in SENSORS:
            entities.append(VolkswagenIDSensor(sensor, car_connectivity, coordinator, index))
    if entities:
        async_add_entities(entities)


class VolkswagenIDSensor(VolkswagenIDBaseEntity, BinarySensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: VolkswagenIdBinaryEntityDescription

    def __init__(
        self,
        sensor: VolkswagenIdBinaryEntityDescription,
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(car_connectivity, coordinator, index)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"{self.data.name} {sensor.name}"
        self._attr_unique_id = f"{self.data.vin}-{sensor.key}"

    @property
    def is_on(self) -> bool:
        """Return true if sensor is on."""
        try:
            state = self.entity_description.value(self.data)
            if isinstance(state, bool):
                return state
            if state.enabled and isinstance(state.value, bool):
                return state.value

            return False

        except KeyError:
            return None
