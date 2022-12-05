# coding=utf-8
import indigo

from ..component import Component


class Temperature(Component):
    """
    The Temperature component handles the monitoring of device's temperature sensors.
    """

    component_type = "temperature"
    device_type_id = "component-temperature"

    def __init__(self, shelly, device_id, comp_id=0):
        """
        Create a Temperature component and assign it to a Shelly device.

        :param shelly: The Shelly device object.
        :param comp_id: The integer identifier for the component
        """
        super(Temperature, self).__init__(shelly, device_id, comp_id)

    def get_device_state_list(self):
        """
        Build the device state list for the device.

        :return: The device state list.
        """
        states = super(Temperature, self).get_device_state_list()
        states.extend([
            indigo.activePlugin.getDeviceStateDictForNumberType("temperature_c", "Temperature", "Temperature"),
            indigo.activePlugin.getDeviceStateDictForNumberType("temperature_f", "Temperature", "Temperature")
        ])

        return states

    def update_state_image(self):
        """
        Update the state image for the device based on current properties.

        The main Indigo device will display battery information, so battery icon
        enumerations should be chosen.

        :return: None
        """
        self.device.updateStateImageOnServer(indigo.kStateImageSel.TemperatureSensorOn)

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """
        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.get_status()

    def handle_notify_event(self, event):
        """
        Handler for events coming from the device.

        :param event: The event from the device.
        :return: None
        """
        super(Temperature, self).handle_notify_event(event)

    def handle_notify_status(self, status):
        """
        Handler for status notifications coming from the device.

        :param status: The status of the component.
        :return: None
        """
        self.process_status(status)

    def get_config(self):
        """
        Get the configuration of the switch.

        :return: config
        """

        self.shelly.publish_rpc("Temperature.GetConfig", {'id': self.comp_id}, callback=self.process_config)

    def process_config(self, config, error=None):
        """
        A method that processes the configuration message.

        :param config: The returned configuration data.
        :param error: Any errors.
        :return: None
        """

        if error:
            self.logger.error(error)
            return

        self.latest_config = {
            'name': config.get("name", ""),
            'report-threshold': config.get("report_thr_C", ""),
        }

        props = self.device.pluginProps
        props.update(self.latest_config)
        self.device.replacePluginPropsOnServer(props)

    def set_config(self, config):
        """
        Set the configuration for the input.

        :param config: An InputConfig object to upload to the device.
        :return: None
        """

        self.shelly.publish_rpc("Temperature.SetConfig", {'id': self.comp_id, 'config': config}, callback=self.process_set_config)

    def process_set_config(self, status, error=None):
        """
        A method that processes the response from setting the config.

        :param status: The status.
        :param error: The error.
        :return: None
        """

        if error:
            self.logger.error("Error writing input configuration: {}".format(error.get("message", "<Unknown>")))
            return

        if status.get('restart_required', False):
            self.log_command_received("rebooting...")

    def get_status(self):
        """
        The status of the Input component contains information about the state
        of the chosen input instance.

        :return: status (dict)
        """

        params = {
            'id': self.comp_id
        }

        self.shelly.publish_rpc("Temperature.GetStatus", params, callback=self.process_status)

    def process_status(self, status, error=None):
        """
        A method that processes the status of the input.

        :param error:
        :param status: The status message
        :return:
        """
        updated_states = []

        temp_c = status.get('tC', None)
        if temp_c is not None:
            updated_states.append({'key': "temperature_c", 'value': temp_c, 'uiValue': "{} °C".format(temp_c), 'decimalPlaces': 1})

        temp_f = status.get('tF', None)
        if temp_f is not None:
            updated_states.append({'key': "temperature_f", 'value': temp_f, 'uiValue': "{} °F".format(temp_f), 'decimalPlaces': 1})

        if self.device.pluginProps["unit"] == "F":
            updated_states.append({'key': "sensorValue", 'value': temp_f, 'uiValue': "{} °F".format(temp_f), 'decimalPlaces': 1})
        elif self.device.pluginProps["unit"] == "C":
            updated_states.append({'key': "sensorValue", 'value': temp_c, 'uiValue': "{} °C".format(temp_c), 'decimalPlaces': 1})

        self.device.updateStatesOnServer(updated_states)
        self.update_state_image()
