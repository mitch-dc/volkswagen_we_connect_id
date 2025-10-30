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
from typing import TYPE_CHECKING

from carconnectivity import carconnectivity
from carconnectivity.commands import GenericCommand
from carconnectivity.command_impl import ChargingStartStopCommand, ClimatizationStartStopCommand
from carconnectivity_connectors.volkswagen.vehicle import VolkswagenElectricVehicle
from carconnectivity_connectors.volkswagen.charging import VolkswagenCharging

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

if TYPE_CHECKING:
    from typing import Optional

@dataclass
class DomainEntry:
    """References to objects shared through hass.data[DOMAIN][config_entry_id]."""

    coordinator: DataUpdateCoordinator[list[VolkswagenElectricVehicle]]
    car_connectivity: carconnectivity.CarConnectivity
    vehicles: list[VolkswagenElectricVehicle]

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
    _car_connectivity = await hass.async_add_executor_job(get_car_connectivity_api,
                                                          get_parameter(entry, "username"),
                                                          get_parameter(entry, "password")
                                                          )

    await hass.async_add_executor_job(update, _car_connectivity)

    async def async_update_data() -> list[VolkswagenElectricVehicle]:
        """Fetch data from Volkswagen API."""

        await hass.async_add_executor_job(update, _car_connectivity)

        vehicles: list[VolkswagenElectricVehicle] = []

        for vehicle in _car_connectivity.garage.list_vehicles():
            if vehicle.model.value in SUPPORTED_VEHICLES:
                vehicles.append(vehicle)

        domain_entry: DomainEntry = hass.data[DOMAIN][entry.entry_id]
        domain_entry.vehicles = vehicles
        return vehicles

    coordinator = DataUpdateCoordinator[list[VolkswagenElectricVehicle]](
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=get_parameter(entry, "update_interval", DEFAULT_UPDATE_INTERVAL_SECONDS),
        ),
    )

    hass.data[DOMAIN][entry.entry_id] = DomainEntry(coordinator, _car_connectivity, [])

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
                _car_connectivity,
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
                set_climatisation_temperature,
                vin,
                _car_connectivity,
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
                _car_connectivity,
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
                    _car_connectivity,
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
def get_car_connectivity_api(username: str, password: str) -> carconnectivity.CarConnectivity:
    """Return a cached carconnectivity api object, shared with the config flow."""

    return carconnectivity.CarConnectivity(
        config={"carConnectivity":{"connectors":[{"type": "volkswagen","config":{"username":username,"password":password}}]}}
    )


_last_successful_api_update_timestamp: float = 0.0
_last_car_connectivity_api: carconnectivity.CarConnectivity | None = None
_update_lock = threading.Lock()


def update(
    api: carconnectivity.CarConnectivity
) -> None:
    """API call to update vehicle information.

    This function is called on its own thread and it is possible for multiple
    threads to call it at the same time, before an earlier carconnectivity update()
    call has finished. When the integration is loaded, multiple platforms
    (binary_sensor, number...) may each call async_config_entry_first_refresh()
    that in turn calls hass.async_add_executor_job() that creates a thread.
    """
    # pylint: disable=global-statement
    global _last_successful_api_update_timestamp, _last_car_connectivity_api

    # Acquire a lock so that only one thread can call api.update() at a time.
    with _update_lock:
        # Skip the update() call altogether if it was last succesfully called
        # in the past 24 seconds (80% of the minimum update interval of 30s).
        elapsed = time.monotonic() - _last_successful_api_update_timestamp
        if elapsed <= 24 and api is _last_car_connectivity_api:
            return
        api.fetch_all()
        _last_successful_api_update_timestamp = time.monotonic()
        _last_car_connectivity_api = api


def start_stop_charging(
    call_data_vin, api: carconnectivity.CarConnectivity, operation: str
) -> bool:
    """Start of stop charging of your volkswagen."""

    if not operation in ("start", "stop"):
        _LOGGER.error("Operation not supported - %s", operation)
        return False
    
    vehicle: Optional[VolkswagenElectricVehicle] = api.garage.get_vehicle(vehicle_id=call_data_vin)
    if vehicle is None:
        _LOGGER.error("Failed to find car - %s", call_data_vin)
        return False

    if (
        vehicle.charging is None
        or not vehicle.charging.state in (VolkswagenCharging.VolkswagenChargingState.UNSUPPORTED)
        or vehicle.charging.commands is None
        or not vehicle.charging.commands.contains_command("start-stop")
        ):
        _LOGGER.error("Vehicle does not support charging - %s", call_data_vin)
        return False
    
    start_stop_command: GenericCommand = vehicle.charging.commands.commands["start-stop"]
    if not isinstance(start_stop_command, ChargingStartStopCommand):
        _LOGGER.error("start-stop command not supported - %s", call_data_vin)
        return False

    try:
        start_stop_command.value = operation
        _LOGGER.info("Sent %s charging call to the vehicle", operation)
    except Exception as exc:
        _LOGGER.error("Failed to send %s charging request to vehicle - %s", operation, exc)
        return False

    return True


def set_ac_charging_speed(
    call_data_vin, api: carconnectivity.CarConnectivity, charging_speed
) -> bool:
    """Set charging speed in your volkswagen."""

    vehicle: Optional[VolkswagenElectricVehicle] = api.garage.get_vehicle(vehicle_id=call_data_vin)
    if vehicle is None:
        _LOGGER.error("Failed to find car - %s", call_data_vin)
        return False

    if charging_speed == vehicle.charging.rate.value:
        _LOGGER.info("Charging speed already set to value %s", charging_speed)
        return True

    try:
        vehicle.charging.rate.value = charging_speed
        _LOGGER.info("Sent charging speed call to the car")
    except Exception as exc:
        _LOGGER.error("Failed to send request to car - %s", exc)
        return False

    return True


def set_target_soc(call_data_vin, api: carconnectivity.CarConnectivity, target_soc: int) -> bool:
    """Set target SOC in your volkswagen."""

    target_soc = int(target_soc)

    if target_soc < 10:
        _LOGGER.error("Target state of charge needs to be at least 10 - %s", target_soc)
        return False

    vehicle: Optional[VolkswagenElectricVehicle] = api.garage.get_vehicle(vehicle_id=call_data_vin)
    if vehicle is None:
        _LOGGER.error("Failed to find car - %s", call_data_vin)
        return False

    if target_soc == vehicle.charging.settings.target_level.value:
        _LOGGER.info("Target state of charge already set to value - %s", target_soc)
        return True

    try:
        vehicle.charging.settings.target_level.value = target_soc
        _LOGGER.info("Sent target SoC call to the car")
    except Exception as exc:
        _LOGGER.error("Failed to send request to car - %s", exc)
        return False

    return True


def set_climatisation_temperature(
    call_data_vin, api: carconnectivity.CarConnectivity, target_temperature: float
) -> bool:
    """Set climate in your volkswagen."""

    if target_temperature < 10:
        _LOGGER.error("Target temperature needs to be at least 10 - %s", target_temperature)
        return False

    vehicle: Optional[VolkswagenElectricVehicle] = api.garage.get_vehicle(vehicle_id=call_data_vin)
    if vehicle is None:
        _LOGGER.error("Failed to find car - %s", call_data_vin)
        return False

    if (
        vehicle.climatization.settings is None
        or not vehicle.climatization.settings.enabled
    ):
        _LOGGER.error("Climatisation settings not supported - %s", call_data_vin)
        return False

    if target_temperature == vehicle.climatization.settings.target_temperature.value:
        _LOGGER.info("Target temperature already set to value - %s", target_temperature)
        return True

    try:
        vehicle.climatization.settings.target_temperature.value = float(target_temperature)
        _LOGGER.info("Sended target temperature call to the car")
    except Exception as exc:
        _LOGGER.error("Failed to send request to car - %s", exc)
        return False

    return True

def start_stop_climatisation(
    call_data_vin, api: carconnectivity.CarConnectivity, operation: str
) -> bool:
    """Set climate in your volkswagen."""

    if not operation in ["start", "stop"]:
        _LOGGER.error("Operation not supported - %s", operation)
        return False

    vehicle: Optional[VolkswagenElectricVehicle] = api.garage.get_vehicle(vehicle_id=call_data_vin)
    if vehicle is None:
        _LOGGER.error("Failed to find car - %s", call_data_vin)
        return False

    if (
        vehicle.climatization.settings is None
        or not vehicle.climatization.settings.enabled
        or not vehicle.climatization.commands.contains_command("start-stop")
    ):
        _LOGGER.error("Climatisation start-stop not supported - %s", call_data_vin)
        return False

    start_stop_command: GenericCommand = vehicle.climatization.commands.commands["start-stop"]
    if not isinstance(start_stop_command, ClimatizationStartStopCommand):
        _LOGGER.error("start-stop climatisation command not supported - %s", call_data_vin)
        return False

    try:
        start_stop_command.value = operation
        _LOGGER.info("Sent climatisation call to car - %s", call_data_vin)
    except Exception as exc:
        _LOGGER.error("Failed to send request to car - %s", exc)
        return False

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        get_car_connectivity_api.cache_clear()
        global _last_car_connectivity_api  # pylint: disable=global-statement
        _last_car_connectivity_api = None

    return unload_ok

# Global lock
volkswagen_car_connectivity_id_lock = asyncio.Lock()

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    # Make sure setup is completed before next unload can be started.
    async with volkswagen_car_connectivity_id_lock:
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
        car_connectivity: carconnectivity.CarConnectivity,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.car_connectivity = car_connectivity
        self.index = index

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"vw{self.data.vin}")},
            manufacturer="Volkswagen",
            model=f"{self.data.model}",  # format because of the ID.3/ID.4 names.
            name=f"Volkswagen {self.data.name} ({self.data.vin})",
        )

    @property
    def data(self) -> VolkswagenElectricVehicle:
        """Shortcut to access coordinator data for the entity."""
        return self.coordinator.data[self.index]
