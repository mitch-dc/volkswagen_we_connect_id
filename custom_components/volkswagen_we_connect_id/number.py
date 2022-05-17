"""Entity representing a Volkswagen number control."""
from __future__ import annotations

from weconnect import weconnect

from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import (
    VolkswagenIDBaseEntity,
    get_object_value,
    set_climatisation,
    set_target_soc,
)
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add buttons for passed config_entry in HA."""
    we_connect: weconnect.WeConnect
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities = []

    for index, vehicle in enumerate(coordinator.data):
        entities.append(TargetSoCNumber(we_connect, coordinator, index))
        entities.append(TargetClimateNumber(we_connect, coordinator, index))
    if entities:
        async_add_entities(entities)


class TargetSoCNumber(VolkswagenIDBaseEntity, NumberEntity):
    """Representation of a Target SoC entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(we_connect, coordinator, index)

        self._coordinator = coordinator
        self._attr_name = f"{self.data.nickname} Target State Of Charge"
        self._attr_unique_id = f"{self.data.vin}-target_state_of_charge"
        self._we_connect = we_connect
        self._attr_min_value = 10
        self._attr_max_value = 100
        self._attr_step = 10

    @property
    def value(self) -> int:
        """Return the current value."""

        return int(
            get_object_value(
                self.data.domains["charging"]["chargingSettings"].targetSOC_pct.value
            )
        )

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        if value > 10:
            await self.hass.async_add_executor_job(
                set_target_soc,
                self.data.vin.value,
                self._we_connect,
                value,
            )


class TargetClimateNumber(VolkswagenIDBaseEntity, NumberEntity):
    """Representation of a Target Climate entity."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(we_connect, coordinator, index)

        self._coordinator = coordinator
        self._attr_name = f"{self.data.nickname} Target Climate Temperature"
        self._attr_unique_id = f"{self.data.vin}-target_climate_temperature"
        self._we_connect = we_connect
        self._attr_min_value = 10
        self._attr_max_value = 30
        self._attr_step = 0.5

    @property
    def value(self) -> float:
        """Return the current value."""
        targetTemp = self.data.domains["climatisation"][
            "climatisationSettings"
        ].targetTemperature_C.value

        return float(targetTemp)

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        if value > 10:
            self._attr_value = value
            await self.hass.async_add_executor_job(
                set_climatisation, self.data.vin.value, self._we_connect, "none", value
            )
