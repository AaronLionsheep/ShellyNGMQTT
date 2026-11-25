import indigo  # pyright: ignore[reportMissingImports, reportMissingModuleSource]

from ..component import Component


class PM1(Component):
    """
    The PM1 component handles a single-phase power meter with no switching
    capability, as found on the Shelly Plus PM Mini.

    Unlike Switch, this component has no output to control. It only reports
    what it measures, so it exposes no actions beyond a status request.
    """

    component_type = "pm1"
    device_type_id = "component-pm1"

    def __init__(self, shelly, device_id, comp_id=0):
        """
        Create a PM1 component and assign it to a ShellyNG device.

        :param shelly: The main ShellyNG device object.
        :param comp_id: The integer identifier for the component
        """

        super().__init__(shelly, device_id, comp_id)

    def get_device_state_list(self):
        """
        Build the device state list for the device.

        :return: The device state list.
        """
        states = super().get_device_state_list()

        states.extend(
            [
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "voltage", "Voltage (volts)", "Voltage (volts)"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "current", "Current (Amps)", "Current (Amps)"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "frequency", "Frequency (Hz)", "Frequency (Hz)"
                ),
                indigo.activePlugin.getDeviceStateDictForNumberType(
                    "returned_energy", "Returned Energy (kWh)", "Returned Energy (kWh)"
                ),
            ]
        )

        return states

    def get_device_display_state_id(self):
        """
        Show the current power draw in the device list.

        A meter has no output, so this component never writes onOffState.
        Left to the default, the device would show a permanent "off" next to a
        live power reading, so display the measurement instead.

        :return: The state name.
        """
        return "curEnergyLevel"

    def update_state_image(self):
        """
        Show the energy meter icon, using the off version when nothing is drawing power.

        The saved power state is used because a NotifyStatus may only include
        the fields that changed.

        :return: None
        """
        # TODO: Loads with small standby readings may need a configurable cutoff.
        power = self.device.states.get("curEnergyLevel", 0) or 0
        image = (
            indigo.kStateImageSel.EnergyMeterOn
            if power > 0
            else indigo.kStateImageSel.EnergyMeterOff
        )
        self.device.updateStateImageOnServer(image)

    def get_config(self):
        """
        Get the configuration of the power meter.

        :return: config
        """

        self.shelly.publish_rpc(
            "PM1.GetConfig", {"id": self.comp_id}, callback=self.process_config
        )

    def process_config(self, config, error=None):
        """
        A method that processes the configuration message.

        :param config: The returned configuration data.
        :param error: Any errors.
        :return: None
        """

        if error:
            self.log_rpc_error("read configuration", error)
            return

        self.latest_config = {
            "name": config.get("name", ""),
        }

        props = self.device.pluginProps
        props.update(self.latest_config)
        self.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the power meter.

        :param config: A config object to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc(
            "PM1.SetConfig",
            {"id": self.comp_id, "config": config},
            callback=self.process_set_config,
        )

    def process_set_config(self, status, error=None):
        """
        A method that processes the response from setting the config.

        :param status: The status.
        :param error: The error.
        :return: None
        """

        if error:
            self.log_rpc_error("write configuration", error)
            return

        if status.get("restart_required", False):
            self.log_command_received("rebooting...")

    def get_status(self):
        """
        The status of the PM1 component contains the instantaneous power,
        voltage, current and frequency, plus the accumulated energy counters.

        :return: status (dict)
        """

        self.shelly.publish_rpc(
            "PM1.GetStatus", {"id": self.comp_id}, callback=self.process_status
        )

    def process_status(self, status, error=None):
        """
        A method that processes the status of the power meter.

        :param status: The status message
        :param error:
        :return:
        """

        if error:
            self.log_rpc_error("read status", error)
            return

        updated_states = []

        # Process Power
        power = status.get("apower", None)
        if power is not None and "curEnergyLevel" in self.device.states:
            updated_states.append(
                {"key": "curEnergyLevel", "value": power, "uiValue": f"{power} W"}
            )

        # Process Voltage
        voltage = status.get("voltage", None)
        if voltage is not None and "voltage" in self.device.states:
            updated_states.append(
                {"key": "voltage", "value": voltage, "uiValue": f"{voltage} V"}
            )

        # Process Current
        current = status.get("current", None)
        if current is not None and "current" in self.device.states:
            updated_states.append(
                {"key": "current", "value": current, "uiValue": f"{current} A"}
            )

        # Process Frequency
        frequency = status.get("freq", None)
        if frequency is not None and "frequency" in self.device.states:
            updated_states.append(
                {"key": "frequency", "value": frequency, "uiValue": f"{frequency} Hz"}
            )

        # Process Energy. The device reports watt-hours, but Indigo's
        # accumEnergyTotal is defined in kilowatt-hours.
        energy_total = status.get("aenergy", {}).get("total", None)
        if energy_total is not None and "accumEnergyTotal" in self.device.states:
            energy_total_kwh = energy_total / 1000
            updated_states.append(
                {
                    "key": "accumEnergyTotal",
                    "value": energy_total_kwh,
                    "uiValue": f"{energy_total_kwh:.3f} kWh",
                }
            )

        # Process Returned Energy, reported for meters that can measure export.
        returned_total = status.get("ret_aenergy", {}).get("total", None)
        if returned_total is not None and "returned_energy" in self.device.states:
            returned_total_kwh = returned_total / 1000
            updated_states.append(
                {
                    "key": "returned_energy",
                    "value": returned_total_kwh,
                    "uiValue": f"{returned_total_kwh:.3f} kWh",
                }
            )

        self.device.updateStatesOnServer(updated_states)
        self.update_state_image()
