"""Entity representing a Volkswagen number control."""
from __future__ import annotations

from carconnectivity import carconnectivity

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import (
    DomainEntry,
    VolkswagenIDBaseEntity,
    get_object_value,
    set_climatisation_temperature,
    set_target_soc,
)
from .const import DOMAIN

from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add buttons for passed config_entry in HA."""
    domain_entry: DomainEntry = hass.data[DOMAIN][config_entry.entry_id]
    car_connectivity = domain_entry.car_connectivity
    coordinator = domain_entry.coordinator

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for index, _ in enumerate(coordinator.data):
        entities.append(TargetSoCNumber(car_connectivity, coordinator, index))
        entities.append(TargetClimateNumber(car_connectivity, coordinator, index))
    if entities:
        async_add_entities(entities)


class TargetSoCNumber(VolkswagenIDBaseEntity, NumberEntity):
    """Representation of a Target SoC entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(car_connectivity, coordinator, index)

        self._coordinator = coordinator
        self._attr_name = f"{self.data.name} Target State Of Charge"
        self._attr_unique_id = f"{self.data.vin}-target_state_of_charge"
        self._attr_icon = "mdi:battery"
        self._car_connectivity = car_connectivity
        self._attr_native_min_value = 10
        self._attr_native_max_value = 100
        self._attr_native_step = 10
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        return int(
            get_object_value(
                self.data.charging.settings.target_level.value
            )
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if value > 10:
            await self.hass.async_add_executor_job(
                set_target_soc,
                self.data.vin.value,
                self._car_connectivity,
                value,
            )


class TargetClimateNumber(VolkswagenIDBaseEntity, NumberEntity):
    """Representation of a Target Climate entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(car_connectivity, coordinator, index)

        self._coordinator = coordinator
        self._attr_name = f"{self.data.name} Target Climate Temperature"
        self._attr_unique_id = f"{self.data.vin}-target_climate_temperature"
        self._attr_icon = "mdi:thermometer"
        self._car_connectivity = car_connectivity
        self._attr_native_min_value = 10
        self._attr_native_max_value = 30
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        targetTemp = self.data.climatization.settings.target_temperature.value

        return float(targetTemp)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if value > 10:
            self._attr_native_value = value
            await self.hass.async_add_executor_job(
                set_climatisation_temperature, self.data.vin.value, self._car_connectivity, value
            )
