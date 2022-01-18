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

PLATFORMS: list[str] = ["sensor", "button"]
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

    await hass.async_add_executor_job(api.update)

    hass.data[DOMAIN][entry.entry_id] = api
    hass.data[DOMAIN][entry.entry_id + "_vehicles"] = api.vehicles
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    @callback
    async def volkswagen_id_set_climatisation(call: ServiceCall) -> None:

        vin = call.data["vin"]
        start_stop = call.data["start_stop"]
        target_temperature = 0
        if "target_temp" in call.data:
            target_temperature = call.data["target_temp"]

        await hass.async_add_executor_job(
            set_climatisation,
            vin,
            api,
            start_stop,
            target_temperature,
        )

    @callback
    async def volkswagen_id_set_target_soc(call: ServiceCall) -> None:

        vin = call.data["vin"]
        target_soc = 0
        if "target_soc" in call.data:
            target_soc = call.data["target_soc"]

        await hass.async_add_executor_job(
            set_target_soc,
            vin,
            api,
            target_soc,
        )

    @callback
    async def volkswagen_id_set_ac_charge_speed(call: ServiceCall) -> None:

        vin = call.data["vin"]
        if "maximum_reduced" in call.data:
            await hass.async_add_executor_job(
                set_ac_charging_speed,
                vin,
                api,
                call.data["maximum_reduced"],
            )

    # Register our services with Home Assistant.
    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_climatisation", volkswagen_id_set_climatisation
    )
    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_target_soc", volkswagen_id_set_target_soc
    )
    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_ac_charge_speed", volkswagen_id_set_ac_charge_speed
    )

    return True


def set_ac_charging_speed(
    callDataVIN, api: weconnect.WeConnect, charging_speed: float
) -> bool:
    """Set charging speed in your volkswagen."""

    api.login()
    api.update()

    for vin, vehicle in api.vehicles.items():
        if vin == callDataVIN:
            if (
                charging_speed
                != vehicle.domains["charging"][
                    "chargingSettings"
                ].maxChargeCurrentAC.value
            ):
                try:
                    vehicle.domains["charging"][
                        "chargingSettings"
                    ].maxChargeCurrentAC.value = charging_speed
                    _LOGGER.info("Sended charging speed call to the car")
                except Exception as exc:
                    _LOGGER.error(
                        exc.args[0]
                        + " - Restart/start the car to reset the rate_limit."
                    )
                    return False

    api.update()

    return True


def set_target_soc(callDataVIN, api: weconnect.WeConnect, target_soc: float) -> bool:
    """Set target SOC in your volkswagen."""

    api.login()
    api.update()

    for vin, vehicle in api.vehicles.items():
        if vin == callDataVIN:
            if (
                target_soc > 10
                and target_soc
                != vehicle.domains["charging"]["chargingSettings"].targetSOC_pct.value
            ):
                try:
                    vehicle.domains["charging"][
                        "chargingSettings"
                    ].targetSOC_pct.value = target_soc
                    _LOGGER.info("Sended target SoC call to the car")
                except Exception as exc:
                    _LOGGER.error(
                        exc.args[0]
                        + " - Restart/start the car to reset the rate_limit."
                    )
                    return False

    api.update()

    return True


def set_climatisation(
    callDataVIN, api: weconnect.WeConnect, operation: str, target_temperature: float
) -> bool:
    """Set climate in your volkswagen."""

    api.login()
    api.update()

    for vin, vehicle in api.vehicles.items():
        if vin == callDataVIN:

            if (
                target_temperature > 10
                and target_temperature
                != vehicle.domains["climatisation"][
                    "climatisationSettings"
                ].targetTemperature_C.value
            ):
                try:
                    vehicle.domains["climatisation"][
                        "climatisationSettings"
                    ].targetTemperature_C.value = target_temperature
                    _LOGGER.info("Sended target temperature call to the car")
                except Exception as exc:
                    _LOGGER.error(
                        exc.args[0]
                        + " - Restart/start the car to reset the rate_limit."
                    )
                    return False

            if operation == "start":
                try:
                    if (
                        vehicle.controls.climatizationControl is not None
                        and vehicle.controls.climatizationControl.enabled
                    ):
                        vehicle.controls.climatizationControl.value = "start"
                        _LOGGER.info("Sended start climate call to the car")
                except Exception as exc:
                    _LOGGER.error(
                        exc.args[0]
                        + " - Restart/start the car to reset the rate_limit."
                    )
                    return False

            if operation == "stop":
                try:
                    if (
                        vehicle.controls.climatizationControl is not None
                        and vehicle.controls.climatizationControl.enabled
                    ):
                        vehicle.controls.climatizationControl.value = "stop"
                        _LOGGER.info("Sended stop climate call to the car")
                except Exception as exc:
                    _LOGGER.error(
                        exc.args[0]
                        + " - Restart/start the car to reset the rate_limit."
                    )
                    return False

    api.update()

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
