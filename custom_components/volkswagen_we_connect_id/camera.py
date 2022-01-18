"""Platform for sensor integration."""
from __future__ import annotations

from datetime import timedelta
import io
import logging

from PIL import Image
from weconnect import weconnect

from homeassistant.components.camera import Camera
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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
        update_interval=timedelta(minutes=60),
    )

    cameras: list[VolkswagenIDCamera] = []
    for vin, vehicle in vehicles.items():
        cameras.append(
            VolkswagenIDCamera(
                vehicle,
                we_connect,
                coordinator,
            )
        )

    if cameras:
        async_add_entities(cameras)


class VolkswagenIDCamera(Camera):
    # Implement one of these methods.

    def __init__(
        self,
        vehicle: weconnect.Vehicle,
        we_connect: weconnect.WeConnect,
        coordinator: DataUpdateCoordinator,
    ) -> None:
        """Initialize VolkswagenID camera."""

        Camera.__init__(self)

        self._attr_name = f"Volkswagen ID {vehicle.nickname} Image"
        self._attr_unique_id = f"{vehicle.vin}-Image"

        self._coordinator = coordinator
        self._we_connect = we_connect
        self._data = f"/vehicles/{vehicle.vin}/pictures/car"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"vw{vehicle.vin}")},
            manufacturer="Volkswagen",
            model=f"{vehicle.model}",  # format because of the ID.3/ID.4 names.
            name=f"Volkswagen {vehicle.nickname}",
        )

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return image response."""
        try:
            image = self._we_connect.getByAddressString(self._data).value
            imgByteArr = io.BytesIO()
            image.save(imgByteArr, format=image.format)
            imgByteArr = imgByteArr.getvalue()
            return imgByteArr

        except FileNotFoundError:
            _LOGGER.warning("Could not read camera %s image from file: %s")
        return None
