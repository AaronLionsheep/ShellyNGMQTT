import indigo
import logging

from Queue import Queue

from shelly.devices.ShellyPlus1 import ShellyPlus1
from shelly.devices.ShellyPlusI4 import ShellyPlusI4

shelly_model_classes = {
    'shelly-plus-1': ShellyPlus1,
    'shelly-plus-i-4': ShellyPlusI4
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.setLogLevel(pluginPrefs.get('log-level', "info"))

        self.shellies = {}
        self.message_types = []
        self.message_queue = Queue()
        self.mqtt_plugin = indigo.server.getPlugin("com.flyingdiver.indigoplugin.mqtt")

        # {
        #   <brokerId>: {
        #       'some/topic': [dev1, dev2, dev3],
        #       'another/topic': [dev1, dev4, dev5]
        #   }
        #   <anotherBroker>: {
        #       'some/topic': [dev6, dev7],
        #       'another/unique/topic': [dev7, dev8, dev9]
        #   }
        # }
        self.broker_device_topics = {}

    def startup(self):
        """

        :return:
        """

        if not self.mqtt_plugin:
            self.logger.error("MQTT Connector plugin is required!!")
            exit(-1)
        indigo.server.subscribeToBroadcast("com.flyingdiver.indigoplugin.mqtt",
                                           "com.flyingdiver.indigoplugin.mqtt-message_queued", "message_handler")

    def shutdown(self):
        pass

    def runConcurrentThread(self):
        """
        Main work thread where messages are continually dequeued and processed.

        :return: None
        """

        try:
            while True:
                if not self.mqtt_plugin.isEnabled():
                    self.logger.error("MQTT Connector plugin not enabled, aborting.")
                    self.sleep(60)
                else:
                    self.process_messages()
                    self.sleep(0.1)

        except self.StopThread:
            pass

    #
    # Message processing
    #

    def message_handler(self, notification):
        """
        Handler to receive and queue messages coming from the mqtt plugin.

        :param notification: The message object.
        :return: None
        """

        if notification['message_type'] in self.message_types:
            self.message_queue.put(notification)

    def process_messages(self):
        """
        Processes messages in the queue until the queue is empty. This is used to pass
        messages that have come from MQTT into the appropriate devices.

        :return: None
        """

        while not self.message_queue.empty():
            # At least 1 of the devices care about this message
            notification = self.message_queue.get()
            if not notification:
                return

            # We have a valid message
            # Find the devices that need to get this message and give it to them
            broker_id = int(notification['brokerID'])
            props = {'message_type': notification['message_type']}
            while True:
                data = self.mqtt_plugin.executeAction("fetchQueuedMessage", deviceId=broker_id, props=props, waitUntilDone=True)
                if data is None:  # Ensure we got data back
                    self.logger.debug("data was none when fetching message")
                    break

                topic = '/'.join(data['topic_parts'])  # transform the topic into a single string
                payload = data['payload']
                message_type = data['message_type']
                self.logger.debug("    Processing: \"%s\" on topic \"%s\"", payload, topic)
                device_topics = self.broker_device_topics.get(broker_id, {})  # get device topics for this broker
                dev_ids = device_topics.get(topic, list())  # get devices listening on this broker for this topic
                for dev_id in dev_ids:
                    shelly = self.shellies.get(dev_id, None)
                    self.logger.debug(shelly)
                    if shelly is not None and message_type == shelly.get_message_type():
                        # Send this message data to the shelly object
                        shelly.handle_message(topic, payload)

    #
    # Device management
    #

    def deviceStartComm(self, device):
        """

        :param device:
        :return:
        """

        self.logger.debug("device starting: {} ({})".format(device.name, device.id))

        if device.deviceTypeId in shelly_model_classes:
            model_class = shelly_model_classes[device.deviceTypeId]
            shelly = model_class(device)
            self.shellies[device.id] = shelly

            # Check that the device has a broker and an address
            if shelly.get_broker_id() is None or shelly.get_address() is None:
                # Ensure the device has a broker and address
                self.logger.error("broker-id: \"{}\" address: \"{}\"".format(shelly.get_broker_id(), shelly.get_address()))
                self.logger.error("\"{}\" is not properly setup! Check the broker and topic root.".format(device.name))
                return False

            # ensure that deviceSubscriptions has a dictionary of subscriptions for the broker
            if shelly.get_broker_id() not in self.broker_device_topics:
                self.broker_device_topics[shelly.get_broker_id()] = {}

            # Add the device id to each topic list
            broker_topics = self.broker_device_topics[shelly.get_broker_id()]
            for topic in shelly.get_topics():
                # See if there is a list of devices already listening to this subscription
                if topic not in broker_topics:
                    # initialize a new list of devices for this subscription
                    broker_topics[topic] = []
                broker_topics[topic].append(shelly.device.id)

            # Store the message type
            self.message_types.append(shelly.get_message_type())

        # Refresh the device's state list and properties that may have changed between plugin versions
        device = indigo.device.changeDeviceTypeId(device, device.deviceTypeId)
        device.replaceOnServer()
        props = device.pluginProps
        device.replacePluginPropsOnServer(props)
        device.stateListOrDisplayStateIdChanged()

        if device.id in self.shellies:
            self.shellies[device.id].get_config()
        else:
            component = self.get_component(device)
            if component:
                component.get_config()

    def deviceStopComm(self, device):
        """

        :param device:
        :return:
        """

        if device.id in self.shellies:
            shelly = self.shellies[device.id]

            # make sure that the device's broker has subscriptions
            if shelly.get_broker_id() in self.broker_device_topics:
                broker_topics = self.broker_device_topics[shelly.get_broker_id()]
                for topic in shelly.get_topics():
                    if topic in broker_topics and shelly.device.id in broker_topics[topic]:
                        broker_topics[topic].remove(shelly.device.id)

                # remove the broker key if there are no more devices using it
                if len(broker_topics) == 0:
                    del self.broker_device_topics[shelly.get_broker_id()]

            self.message_types.remove(shelly.get_message_type())

        if device.id in self.shellies:
            del self.shellies[device.id]

    def getDeviceFactoryUiValues(self, devIdList):
        """

        :param devIdList:
        :return:
        """

        values_dict = indigo.Dict()
        errors_dict = indigo.Dict()

        main_device = None
        # Find the main device in the group
        for dev_id in devIdList:
            device = indigo.devices[dev_id]
            self.logger.info(device.deviceTypeId)
            if device.deviceTypeId in shelly_model_classes:
                main_device = device
                break

        if main_device is not None:
            values_dict['shelly-model'] = main_device.deviceTypeId
            values_dict['broker-id'] = main_device.pluginProps['broker-id']
            values_dict['address'] = main_device.pluginProps['address']
            values_dict['message-type'] = main_device.pluginProps['message-type']

        return values_dict, errors_dict

    def validateDeviceFactoryUi(self, valuesDict, devIdList):
        """

        :param valuesDict: The data the user is attempting to submit from the device factory UI.
        :param devIdList:
        :return: Tuple of validity, data to load into the form, and any error messages.
        """

        errors_dict = indigo.Dict()
        valid = True
        group_device_types = [indigo.devices[dev_id].deviceTypeId for dev_id in devIdList]

        # Ensure a model is selected
        if valuesDict['shelly-model'] == "":
            valid = False
            errors_dict['shelly-model'] = "You must select the device model!"
        else:
            # Ensure the main model is not changing
            main_models = set(group_device_types).intersection(set(shelly_model_classes.keys()))
            if len(main_models) == 1:
                # The selected model bust be the same
                main_model = main_models.pop()
                if valuesDict['shelly-model'] != main_model:
                    valid = False
                    errors_dict['shelly-model'] = "You can not change the main model!"

        # Ensure a broker is selected
        if valuesDict['broker-id'] == "":
            valid = False
            errors_dict['broker-id'] = "You must select the broker the device will connect to!"

        # Ensure the device address is supplied
        if valuesDict['address'] == "":
            valid = False
            errors_dict['address'] = "You must specify the base device address!"

        # Ensure the message type is supplied
        if valuesDict['message-type'] == "":
            valid = False
            errors_dict['message-type'] = "You must specify the message type for the device!"

        return valid, valuesDict, errors_dict

    def closedDeviceFactoryUi(self, valuesDict, userCancelled, devIdList):
        """

        :param valuesDict:
        :param userCancelled:
        :param devIdList:
        :return:
        """

        if userCancelled:
            return

        shelly_model = valuesDict['shelly-model']
        group_models = [indigo.devices[dev_id].model for dev_id in devIdList]
        model_class = shelly_model_classes.get(shelly_model, None)
        if model_class is None:
            self.logger.error("Unable to find class for device with type: '{}'".format(shelly_model))

        device = None
        device_props = {
            'broker-id': valuesDict["broker-id"],
            'address': valuesDict["address"],
            'message-type': valuesDict["message-type"]
        }
        if model_class.display_name not in group_models:
            # The main device is not in the group, so create one
            device = indigo.device.create(indigo.kProtocol.Plugin, deviceTypeId=shelly_model, props=device_props)
            self.logger.info("device created...")
            device.model = model_class.display_name
            device.replaceOnServer()
        else:
            # Find the main device in the group
            for dev_id in devIdList:
                device = indigo.devices[dev_id]
                if device.deviceTypeId == shelly_model:
                    break

        # Make sure we actually have a main device
        if device is None:
            self.logger.error("Unable to create or find the main device!")
            return

        # Update the device properties from the factory UI
        self.logger.info(device_props)
        device.replacePluginPropsOnServer(device_props)

        # Initialize the device and its components to populate the already opened UI
        model_class(device)

        return

    def validateDeviceConfigUi(self, values_dict, type_id, dev_id):
        """

        :param valuesDict:
        :param typeId:
        :param devId:
        :return:
        """

        return True, values_dict

    def closedDeviceConfigUi(self, values_dict, user_cancelled, type_id, dev_id):
        """

        :param values_dict:
        :param user_cancelled:
        :param type_id:
        :param dev_id:
        :return:
        """

        # When a config is changed then the device already tries to get the config
        # TODO: Determine if the device needs to be restarted from the config change
        """
        if dev_id in self.shellies:
            self.shellies[dev_id].get_config()
        else:
            component = self.get_component(indigo.devices[dev_id])
            if component:
                self.logger.info("Getting config of component: {} ({})".format(component, component.device.name))
                component.get_config()
            else:
                self.logger.error("Unable to find shelly or component for device id: {}".format(dev_id))
        """
        pass

    def actionControlDevice(self, action, device):
        """
        Handles an action being performed on the device.

        :param action: The action that occurred.
        :param device: The device that was acted on.
        :return: None
        """

        shelly = self.shellies.get(device.id, None)
        if shelly is not None:
            shelly.handle_action(action)
        else:
            component = self.get_component(device)
            if component is not None:
                component.handle_action(action)

    def actionControlUniversal(self, action, device):
        """
        Handles an action being performed on the device.

        :param action: The action that occurred.
        :param device: The device that was acted on.
        :return: None
        """

        shelly = self.shellies.get(device.id, None)
        if shelly is not None:
            shelly.handle_action(action)
        else:
            component = self.get_component(device)
            if component is not None:
                component.handle_action(action)

    def getDeviceStateList(self, device):
        shelly = self.shellies.get(device.id, None)
        if shelly:
            return shelly.get_device_state_list()
        else:
            return indigo.PluginBase.getDeviceStateList(self, device)

    #
    # Plugin utilities
    #

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        """
        Handler for the closing of a configuration UI.

        :param valuesDict: The values in the config.
        :param userCancelled: True or false to indicate if the config was cancelled.
        :return:
        """

        if userCancelled is False:
            self.setLogLevel(valuesDict.get('log-level', "info"))

    def get_broker_devices(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Gets a list of available broker devices.

        :param filter:
        :param valuesDict:
        :param typeId:
        :param targetId:
        :return: A list of brokers.
        """

        brokers = []
        for dev in indigo.devices.iter():
            if dev.protocol == indigo.kProtocol.Plugin and \
                    dev.pluginId == "com.flyingdiver.indigoplugin.mqtt" and \
                    dev.deviceTypeId != 'aggregator':
                brokers.append((dev.id, dev.name))

        brokers.sort(key=lambda tup: tup[1])
        return brokers

    def get_component(self, device):
        """
        Gets the component tied to a device.

        :param device: The indigo device.
        :return: Component object for the device.
        """

        for shelly in self.shellies.values():
            component = shelly.get_component_for_device(device)
            if component is not None:
                return component
        return None

    def setLogLevel(self, level):
        """
        Helper method to set the logging level.

        :param level: Expected to be a string with a valid log level.
        :return: None
        """

        valid_log_levels = ["debug", "info", "warning"]
        if level not in valid_log_levels:
            self.logger.error(u"Attempted to set the log level to an unhandled value: {}".format(level))

        if level == "debug":
            self.indigo_log_handler.setLevel(logging.DEBUG)
            self.logger.debug(u"Log level set to debug")
        elif level == "info":
            self.indigo_log_handler.setLevel(logging.INFO)
            self.logger.info(u"Log level set to info")
        elif level == "warning":
            self.indigo_log_handler.setLevel(logging.WARNING)
            self.logger.warning(u"Log level set to warning")

    #
    # Device Configuration Callbacks
    #

    def _write_system_configuration(self, values_dict, type_id, dev_id):
        """
        Handler for writing the system component's configuration.

        :param values_dict:
        :param type_id:
        :param dev_id:
        :return:
        """

        config = {
            'device': {
                'name': values_dict.get("system-device-name"),
                'eco_mode': values_dict.get("system-device-eco-mode")
            },
            'location': {
                'tz': values_dict.get("system-location-timezone"),
                'lat': values_dict.get("system-location-lat"),
                'lon': values_dict.get("system-location-lon")
            },
            'debug': {
                'mqtt': {
                    'enable': values_dict.get("system-debug-mqtt")
                },
                'websocket': {
                    'enable': values_dict.get("system-debug-mqtt")
                },
                'udp': {
                    'addr': values_dict.get("system-debug-udp-address")
                }
            }
        }

        if len(config['device']['name']) == 0:
            config['device']['name'] = None
        if len(config['location']['tz']) == 0:
            config['location']['tz'] = None
        if config['location']['lat'] == "":
            config['location']['lat'] = None
        if config['location']['lon'] == "":
            config['location']['lon'] = None
        if len(config['debug']['udp']['addr']) == 0:
            config['debug']['udp']['addr'] = None

        self.shellies[dev_id].system.set_config(config)

    def _write_switch_configuration(self, values_dict, type_id, dev_id):
        """
        Handler for writing the switch component's configuration.

        :param values_dict:
        :param type_id:
        :param dev_id:
        :return:
        """

        switch = self.get_component(indigo.devices[dev_id])

        config = {
            'name': values_dict.get("name", ""),
            'in_mode': values_dict.get("in-mode", ""),
            'initial_state': values_dict.get("initial-state", ""),
            'auto_on': values_dict.get("auto-on", False),
            'auto_on_delay': values_dict.get("auto-on-delay", ""),
            'auto_off': values_dict.get("auto-off", False),
            'auto_off_delay': values_dict.get("auto-off-delay", ""),
            'input_id': values_dict.get("input-id", ""),
            'power_limit': values_dict.get("power-limit", ""),
            'voltage_limit': values_dict.get("voltage-limit", ""),
            'current_limit': values_dict.get("current-limit", ""),
        }

        if len(config['name']) == 0:
            config['name'] = None

        switch.set_config(config)

    def _write_input_configuration(self, values_dict, type_id, dev_id):
        """
        Handler for writing the input component's configuration.

        :param values_dict:
        :param type_id:
        :param dev_id:
        :return:
        """

        input_component = self.get_component(indigo.devices[dev_id])

        config = {
            'name': values_dict.get("name", ""),
            'type': values_dict.get("type", ""),
            'invert': values_dict.get("invert", False)
        }

        if len(config['name']) == 0:
            config['name'] = None

        input_component.set_config(config)
