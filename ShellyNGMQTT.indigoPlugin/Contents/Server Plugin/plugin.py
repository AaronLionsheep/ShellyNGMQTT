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

        :param message: The message object.
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
                        # self.logger.debug("        \"%s\" handling \"%s\" on \"%s\"", shelly.device.name, payload, topic)
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
                self.logger.error("brokerId: \"{}\" address: \"{}\"".format(shelly.get_broker_id(), shelly.get_address()))
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

        self.logger.debug("getDeviceFactoryUiValues")
        valuesDict = indigo.Dict()
        errorMsgDict = indigo.Dict()
        return (valuesDict, errorMsgDict)

    def validateDeviceFactoryUi(self, valuesDict, devIdList):
        """

        :param valuesDict:
        :param devIdList:
        :return:
        """

        errorsDict = indigo.Dict()
        return (True, valuesDict, errorsDict)

    def closedDeviceFactoryUi(self, valuesDict, userCancelled, devIdList):
        """

        :param valuesDict:
        :param userCancelled:
        :param devIdList:
        :return:
        """

        if userCancelled:
            return

        if valuesDict["shelly-model"] == "shelly-plus-1":
            device = indigo.device.create(indigo.kProtocol.Plugin, deviceTypeId="shelly-plus-1")
            device.model = "Shelly Plus 1"
            device.replaceOnServer()

            device_props = device.pluginProps
            device_props["broker-id"] = valuesDict["broker-id"]
            device.replacePluginPropsOnServer(device_props)

            # Initialize the device and its components
            ShellyPlus1(device)
        elif valuesDict["shelly-model"] == "shelly-plus-i-4":
            device = indigo.device.create(indigo.kProtocol.Plugin, deviceTypeId="shelly-plus-i-4")
            device.model = "Shelly Plus I4"
            device.replaceOnServer()

            device_props = device.pluginProps
            device_props["broker-id"] = valuesDict["broker-id"]
            device.replacePluginPropsOnServer(device_props)

            # Initialize the device and its components
            ShellyPlusI4(device)

        return

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        """

        :param valuesDict:
        :param typeId:
        :param devId:
        :return:
        """

        return (True, valuesDict)

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

        :param device: THe indigo device.
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
