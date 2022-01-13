"""The Volkswagen We Connect ID integration."""
from __future__ import annotations

import logging
from typing import Any

from weconnect import weconnect
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.vehicle import Vehicle

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

PLATFORMS: list[str] = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Volkswagen We Connect ID from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    api = weconnect.WeConnect(
        username=entry.data["username"],
        password=entry.data["password"],
        updateAfterLogin=False,
        loginOnInit=False,
    )

    hass.data[DOMAIN][entry.entry_id] = api
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    @callback
    async def volkswagen_id_set_climatisation(call: ServiceCall) -> None:

        target_temperature = 0
        if hasattr(call, "target_temp"):
            target_temperature = call.data["target_temp"]

        operation = ControlOperation.START
        if call.data["start_stop"] == "stop":
            operation = ControlOperation.STOP

        # await hass.async_add_executor_job(api.update)
        for vin, vehicle in api.vehicles.items():
            if vin == call.data["vin"]:
                return await hass.async_add_executor_job(
                    set_climatisation, vehicle, operation, target_temperature
                )

    # Register our service with Home Assistant.
    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_climatisation", volkswagen_id_set_climatisation
    )


def set_climatisation(
    vehicle: Vehicle, operation: ControlOperation, target_temperature: float
) -> bool:
    """Set climate in your volkswagen."""

    if (
        target_temperature > 10
        and target_temperature
        != vehicle.domains["climatisation"][
            "climatisationSettings"
        ].targetTemperature_C.value
    ):
        vehicle.domains["climatisation"][
            "climatisationSettings"
        ].targetTemperature_C.value = target_temperature
        _LOGGER.info("Sended target temperature call to the car")

    if (
        operation == ControlOperation.START
        and vehicle.domains["climatisation"][
            "climatisationStatus"
        ].climatisationState.value
        != "heating"
    ):
        try:
            vehicle.controls.climatizationControl.value = ControlOperation.START
        except Exception as exc:
            _LOGGER.error(
                exc.args[0] + " - Restart/start the car to reset the rate_limit."
            )
            return False
        else:
            _LOGGER.info("Sended start climate call to the car")

    elif (
        operation == ControlOperation.STOP
        and vehicle.domains["climatisation"][
            "climatisationStatus"
        ].climatisationState.value
        == "heating"
    ):
        try:
            vehicle.controls.climatizationControl.value = ControlOperation.START
        except Exception as exc:
            _LOGGER.error(exc.args[0])
            return False
        else:
            _LOGGER.info("Sended stop climate call to the car")
        vehicle.controls.climatizationControl.value = ControlOperation.STOP

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class VolkswagenIDBaseEntity(Entity):
    """Common base for VolkswagenID entities."""

    _attr_should_poll = False
    _attr_attribution = "Data provided by Volkswagen Connect ID"

    def __init__(
        self,
        vehicle,
        data,
        we_connect: weconnect.WeConnect,
        coordinator: CoordinatorEntity,
    ) -> None:
        """Initialize sensor."""
        self._data = data
        self._we_connect = we_connect
        self._vehicle = vehicle
        self._coordinator = coordinator
        self._attrs: dict[str, Any] = {
            "car": f"{self._vehicle.nickname}",
            "vin": f"{self._vehicle.vin}",
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"vw{vehicle.vin}")},
            manufacturer="Volkswagen",
            name=f"Volkswagen {vehicle.nickname}",
        )

    async def async_added_to_hass(self):
        """When entity is added to hass."""

        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity. Only used by the generic entity update service."""

        await self._coordinator.async_request_refresh()
