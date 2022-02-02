"""Button integration."""
from weconnect import weconnect
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.vehicle import Vehicle

from homeassistant.components.button import ButtonEntity

from . import set_ac_charging_speed, set_climatisation
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add buttons for passed config_entry in HA."""
    we_connect = hass.data[DOMAIN][config_entry.entry_id]
    vehicles = hass.data[DOMAIN][config_entry.entry_id + "_vehicles"]

    entities = []
    for vin, vehicle in vehicles.items():  # weConnect.vehicles.items():
        entities.append(VolkswagenIDStartClimateButton(vin, vehicle, we_connect))
        entities.append(VolkswagenIDToggleACChargeSpeed(vin, vehicle, we_connect))

    async_add_entities(entities)

    return True


class VolkswagenIDStartClimateButton(ButtonEntity):
    """Button for starting climate."""

    def __init__(self, vin, vehicle, we_connect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"Volkswagen ID {vehicle.nickname} Start Climate"
        self._attr_unique_id = f"{vin}-start_climate"
        self._we_connect = we_connect
        self._vehicle = vehicle

    def press(self) -> None:
        """Handle the button press."""
        set_climatisation(self._vehicle.vin.value, self._we_connect, "start", 0)


class VolkswagenIDToggleACChargeSpeed(ButtonEntity):
    """Button for toggling the charge speed."""

    def __init__(self, vin, vehicle: Vehicle, we_connect: weconnect.WeConnect) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        self._attr_name = f"Volkswagen ID {vehicle.nickname} Toggle AC Charge Speed"
        self._attr_unique_id = f"{vin}-toggle_ac_charge_speed"
        self._we_connect = we_connect
        self._vehicle = vehicle

        self._data = f"/vehicles/{vehicle.vin}/domains/charging/chargingSettings/maxChargeCurrentAC"

    def press(self) -> None:
        """Handle the button press."""

        current_state = self._we_connect.getByAddressString(self._data)

        while hasattr(current_state, "value"):
            current_state = current_state.value

        if current_state == ChargingSettings.MaximumChargeCurrent.MAXIMUM.value:
            set_ac_charging_speed(
                self._vehicle.vin.value,
                self._we_connect,
                ChargingSettings.MaximumChargeCurrent.REDUCED.value,
            )
        else:
            set_ac_charging_speed(
                self._vehicle.vin.value,
                self._we_connect,
                ChargingSettings.MaximumChargeCurrent.MAXIMUM.value,
            )
