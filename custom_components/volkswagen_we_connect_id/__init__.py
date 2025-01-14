"""The Volkswagen We Connect ID integration."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import functools
import logging
import threading
import time
from typing import Any

from weconnect import weconnect
from weconnect.elements.vehicle import Vehicle
from weconnect.elements.control_operation import ControlOperation

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, DEFAULT_UPDATE_INTERVAL_SECONDS

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.DEVICE_TRACKER,
]

_LOGGER = logging.getLogger(__name__)

SUPPORTED_VEHICLES = ["ID.3", "ID.4", "ID.5", "ID. Buzz", "ID.7 Limousine", "ID.7 Tourer"]


@dataclass
class DomainEntry:
    """References to objects shared through hass.data[DOMAIN][config_entry_id]."""

    coordinator: DataUpdateCoordinator[list[Vehicle]]
    we_connect: weconnect.WeConnect
    vehicles: list[Vehicle]

def get_parameter(config_entry: ConfigEntry, parameter: str, default_val: Any = None):
    """Get parameter from OptionsFlow or ConfigFlow"""
    if parameter in config_entry.options.keys():
        return config_entry.options.get(parameter)
    if parameter in config_entry.data.keys():
        return config_entry.data.get(parameter)
    return default_val

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Volkswagen We Connect ID from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    _we_connect = get_we_connect_api(
        username=get_parameter(entry, "username"),
        password=get_parameter(entry, "password"),
    )

    await hass.async_add_executor_job(_we_connect.login)
    await hass.async_add_executor_job(update, _we_connect)

    async def async_update_data() -> list[Vehicle]:
        """Fetch data from Volkswagen API."""

        await hass.async_add_executor_job(update, _we_connect)

        vehicles: list[Vehicle] = []

        for vin, vehicle in _we_connect.vehicles.items():
            if vehicle.model.value in SUPPORTED_VEHICLES:
                vehicles.append(vehicle)

        domain_entry: DomainEntry = hass.data[DOMAIN][entry.entry_id]
        domain_entry.vehicles = vehicles
        return vehicles

    coordinator = DataUpdateCoordinator[list[Vehicle]](
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=get_parameter(entry, "update_interval", DEFAULT_UPDATE_INTERVAL_SECONDS),
        ),
    )

    hass.data[DOMAIN][entry.entry_id] = DomainEntry(coordinator, _we_connect, [])

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    # Setup components
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    async def volkswagen_id_start_stop_charging(call: ServiceCall) -> None:

        vin = call.data["vin"]
        start_stop = call.data["start_stop"]

        if (
            await hass.async_add_executor_job(
                start_stop_charging,
                vin,
                _we_connect,
                start_stop,
            )
            is False
        ):
            _LOGGER.error("Cannot send charging request to car")

    @callback
    async def volkswagen_id_set_climatisation(call: ServiceCall) -> None:

        vin = call.data["vin"]
        start_stop = call.data["start_stop"]
        target_temperature = 0
        if "target_temp" in call.data:
            target_temperature = call.data["target_temp"]

        if (
            await hass.async_add_executor_job(
                set_climatisation,
                vin,
                _we_connect,
                start_stop,
                target_temperature,
            )
            is False
        ):
            _LOGGER.error("Cannot send climate request to car")

    @callback
    async def volkswagen_id_set_target_soc(call: ServiceCall) -> None:

        vin = call.data["vin"]
        target_soc = 0
        if "target_soc" in call.data:
            target_soc = call.data["target_soc"]

        if (
            await hass.async_add_executor_job(
                set_target_soc,
                vin,
                _we_connect,
                target_soc,
            )
            is False
        ):
            _LOGGER.error("Cannot send target soc request to car")

    @callback
    async def volkswagen_id_set_ac_charge_speed(call: ServiceCall) -> None:

        vin = call.data["vin"]
        if "maximum_reduced" in call.data:
            if (
                await hass.async_add_executor_job(
                    set_ac_charging_speed,
                    vin,
                    _we_connect,
                    call.data["maximum_reduced"],
                )
                is False
            ):
                _LOGGER.error("Cannot send ac speed request to car")

    # Register our services with Home Assistant.
    hass.services.async_register(
        DOMAIN, "volkswagen_id_start_stop_charging", volkswagen_id_start_stop_charging
    )

    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_climatisation", volkswagen_id_set_climatisation
    )
    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_target_soc", volkswagen_id_set_target_soc
    )
    hass.services.async_register(
        DOMAIN, "volkswagen_id_set_ac_charge_speed", volkswagen_id_set_ac_charge_speed
    )

    # Reload entry if configuration has changed
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


@functools.lru_cache(maxsize=1)
def get_we_connect_api(username: str, password: str) -> weconnect.WeConnect:
    """Return a cached weconnect api object, shared with the config flow."""
    return weconnect.WeConnect(
        username=username,
        password=password,
        updateAfterLogin=False,
        loginOnInit=False,
        timeout=10,
        updatePictures=False,
    )


_last_successful_api_update_timestamp: float = 0.0
_last_we_connect_api: weconnect.WeConnect | None = None
_update_lock = threading.Lock()


def update(
    api: weconnect.WeConnect
) -> None:
    """API call to update vehicle information.

    This function is called on its own thread and it is possible for multiple
    threads to call it at the same time, before an earlier weconnect update()
    call has finished. When the integration is loaded, multiple platforms
    (binary_sensor, number...) may each call async_config_entry_first_refresh()
    that in turn calls hass.async_add_executor_job() that creates a thread.
    """
    # pylint: disable=global-statement
    global _last_successful_api_update_timestamp, _last_we_connect_api

    # Acquire a lock so that only one thread can call api.update() at a time.
    with _update_lock:
        # Skip the update() call altogether if it was last succesfully called
        # in the past 24 seconds (80% of the minimum update interval of 30s).
        elapsed = time.monotonic() - _last_successful_api_update_timestamp
        if elapsed <= 24 and api is _last_we_connect_api:
            return
        api.update(updatePictures=False)
        _last_successful_api_update_timestamp = time.monotonic()
        _last_we_connect_api = api


def start_stop_charging(
    call_data_vin, api: weconnect.WeConnect, operation: str
) -> bool:
    """Start of stop charging of your volkswagen."""

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:

            if operation == "start":
                try:
                    if (
                        vehicle.controls.chargingControl is not None
                        and vehicle.controls.chargingControl.enabled
                    ):
                        vehicle.controls.chargingControl.value = ControlOperation.START
                        _LOGGER.info("Sended start charging call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False

            if operation == "stop":
                try:
                    if (
                        vehicle.controls.chargingControl is not None
                        and vehicle.controls.chargingControl.enabled
                    ):
                        vehicle.controls.chargingControl.value = ControlOperation.STOP
                        _LOGGER.info("Sended stop charging call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False
    return True


def set_ac_charging_speed(
    call_data_vin, api: weconnect.WeConnect, charging_speed
) -> bool:
    """Set charging speed in your volkswagen."""

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:
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
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False

    return True


def set_target_soc(call_data_vin, api: weconnect.WeConnect, target_soc: int) -> bool:
    """Set target SOC in your volkswagen."""

    target_soc = int(target_soc)

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:
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
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False
    return True


def set_climatisation(
    call_data_vin, api: weconnect.WeConnect, operation: str, target_temperature: float
) -> bool:
    """Set climate in your volkswagen."""

    for vin, vehicle in api.vehicles.items():
        if vin == call_data_vin:

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
                    ].targetTemperature_C.value = float(target_temperature)
                    _LOGGER.info("Sended target temperature call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False

            if operation == "start":
                try:
                    if (
                        vehicle.controls.climatizationControl is not None
                        and vehicle.controls.climatizationControl.enabled
                    ):
                        vehicle.controls.climatizationControl.value = (
                            ControlOperation.START
                        )
                        _LOGGER.info("Sended start climate call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False

            if operation == "stop":
                try:
                    if (
                        vehicle.controls.climatizationControl is not None
                        and vehicle.controls.climatizationControl.enabled
                    ):
                        vehicle.controls.climatizationControl.value = (
                            ControlOperation.STOP
                        )
                        _LOGGER.info("Sended stop climate call to the car")
                except Exception as exc:
                    _LOGGER.error("Failed to send request to car - %s", exc)
                    return False
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        get_we_connect_api.cache_clear()
        global _last_we_connect_api  # pylint: disable=global-statement
        _last_we_connect_api = None

    return unload_ok

# Global lock
volkswagen_we_connect_id_lock = asyncio.Lock()

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    # Make sure setup is completed before next unload can be started.
    async with volkswagen_we_connect_id_lock:
        await async_unload_entry(hass, entry)
        await async_setup_entry(hass, entry)

def get_object_value(value) -> str:
    """Get value from object or enum."""

    while hasattr(value, "value"):
        value = value.value

    return value


class VolkswagenIDBaseEntity(CoordinatorEntity):
    """Common base for VolkswagenID entities."""

    # _attr_should_poll = False
    _attr_attribution = "Data provided by Volkswagen Connect ID"

    def __init__(
        self,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.we_connect = we_connect
        self.index = index

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"vw{self.data.vin}")},
            manufacturer="Volkswagen",
            model=f"{self.data.model}",  # format because of the ID.3/ID.4 names.
            name=f"Volkswagen {self.data.nickname} ({self.data.vin})",
        )

    @property
    def data(self):
        """Shortcut to access coordinator data for the entity."""
        return self.coordinator.data[self.index]
