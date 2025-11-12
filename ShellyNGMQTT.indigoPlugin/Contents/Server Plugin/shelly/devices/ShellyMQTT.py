import indigo # noqa
import json
import logging
import uuid

from .Shelly import Shelly


class ShellyMQTT(Shelly):
    """
    Base class used by all Shelly MQTT model classes.
    """

    display_name = "ShellyMQTTBase"

    def __init__(self, device_id):
        """Create a new Shelly device.

        :param device_id: The indigo device id.
        """
        super(ShellyMQTT, self).__init__(device_id)

        self.functional_components = []
        self.system_components = {}
        self.rpc_callbacks = {}

    @property
    def components(self):
        """
        Getter for all functional and system components.

        :return: A list of all functional and system components.
        """
        return self.functional_components + list(self.system_components.values())

    #
    # Property getters
    #

    def get_broker_id(self):
        """
        Gets the Indigo deviceId of the broker that this device connects to.

        :return: The Indigo deviceId of the broker for this device.
        """

        broker_id = self.device.pluginProps.get('broker-id', None)
        if broker_id is None or broker_id == '':
            return None
        else:
            return int(broker_id)

    def get_message_type(self):
        """
        Helper method to get the message type that this device will process.

        :return: The message type for this device.
        """

        return self.device.pluginProps.get('message-type', "")

    def get_topics(self):
        """
        A list of topics that the device subscribes to.

        :return: A list.
        """

        address = self.get_address()
        if address is None:
            return []
        else:
            return [
                "{}/online".format(address),
                "{}/rpc".format(address),
                "{}/events/rpc".format(address)
            ]

    def get_device_state_list(self):
        """
        Build the device state list for the device.

        Possible state helpers are:
        - getDeviceStateDictForNumberType
        - getDeviceStateDictForRealType
        - getDeviceStateDictForStringType
        - getDeviceStateDictForBoolOnOffType
        - getDeviceStateDictForBoolYesNoType
        - getDeviceStateDictForBoolOneZeroType
        - getDeviceStateDictForBoolTrueFalseType

        :return: The device state list.
        """
        states = super(ShellyMQTT, self).get_device_state_list()
        states.extend([
            indigo.activePlugin.getDeviceStateDictForBoolYesNoType("online", "Online", "Online"),
            indigo.activePlugin.getDeviceStateDictForStringType("ip-address", "IP Address", "IP Address"),
            indigo.activePlugin.getDeviceStateDictForStringType("ssid", "Connected SSID", "Connected SSID"),
            indigo.activePlugin.getDeviceStateDictForNumberType("rssi", "WiFi Signal Strength (dBms)", "WiFi Signal Strength (dBms)"),
            indigo.activePlugin.getDeviceStateDictForStringType("mac-address", "Mac Address", "Mac Address"),
            indigo.activePlugin.getDeviceStateDictForNumberType("uptime", "Uptime (seconds)", "Uptime (seconds)"),
            indigo.activePlugin.getDeviceStateDictForStringType("available-firmware", "Available Firmware Version", "Available Firmware Version"),
            indigo.activePlugin.getDeviceStateDictForStringType("available-beta-firmware", "Available Beta Firmware Version", "Available Beta Firmware Version"),
            indigo.activePlugin.getDeviceStateDictForStringType("current-firmware", "Current Firmware Version", "Current Firmware Version"),
        ])
        return states

    #
    # MQTT Utilities
    #

    def get_mqtt(self):
        """
        Helper function to get the MQTT plugin instance.

        :return: The MQTT Connector plugin if it is running, otherwise None.
        """

        mqtt = indigo.server.getPlugin("com.flyingdiver.indigoplugin.mqtt")
        if not mqtt.isEnabled():
            self.logger.error("MQTT plugin must be enabled!")
            return None
        else:
            return mqtt

    def subscribe(self):
        """
        Subscribes the device to all required topics on the specified broker.

        :return: None
        """

        mqtt = self.get_mqtt()
        if mqtt is not None:
            for topic in self.get_topics():
                props = {
                    'topic': topic,
                    'qos': 0
                }
                mqtt.executeAction("add_subscription", deviceId=self.get_broker_id(), props=props)

    def publish(self, topic, payload):
        """
        Publishes a message on a given topic to the device's broker.

        :param topic: The topic to send data to.
        :param payload: The data to send over the topic.
        :return: None
        """

        mqtt = self.get_mqtt()
        if mqtt is not None:
            props = {
                'topic': topic,
                'payload': payload,
                'qos': 0,
                'retain': 0,
            }
            mqtt.executeAction("publish", deviceId=self.get_broker_id(), props=props, waitUntilDone=False)
            self.logger.debug("\"%s\" published \"%s\" to \"%s\"", self.device.name, payload, topic)

    def publish_rpc(self, method: str, params: dict = None, callback=None) -> None:
        """

        :return:
        """

        rpc_id = uuid.uuid4().hex
        if not params:
            params = {}
        if callback:
            self.rpc_callbacks[rpc_id] = callback
        rpc = {
            'id': rpc_id,
            'src': self.get_address(),
            'method': method,
            'params': params
        }
        self.publish("{}/rpc".format(self.get_address()), json.dumps(rpc))

    #
    # Handlers
    #

    def handle_message(self, topic, payload):
        """
        The default handler for incoming messages.
        These are messages that are handled by ANY Shelly device.

        :param topic: The topic of the incoming message.
        :param payload: The content of the massage.
        :return:  None
        """

        if topic == "{}/online".format(self.get_address()):
            is_online = (payload == "true")
            self.device.updateStateOnServer(key='online', value=is_online)
        elif topic == "{}/rpc".format(self.get_address()):
            rpc = json.loads(payload)
            # Only process a response, which does not have a method
            if 'method' not in rpc:
                rpc_id = rpc.get('id', None)
                result = rpc.get('result', None)
                error = rpc.get('error', None)
                callback = self.rpc_callbacks.get(rpc_id, None)
                if callback:
                    callback(result, error)
                    del self.rpc_callbacks[rpc_id]
        elif topic == "{}/events/rpc".format(self.get_address()):
            rpc = json.loads(payload)
            method = rpc.get('method', None)
            params = rpc.get('params', {})

            if method in ("NotifyStatus", "NotifyFullStatus"):
                for component in params.keys():
                    # Ignore the timestamp since it is not a component
                    if component == "ts":
                        continue

                    # Parse the component type and instance ID
                    component_type = None
                    instance_id = None
                    if ':' in component:
                        component_parts = component.split(':')
                        if len(component_parts) == 2:
                            component_type = component_parts[0]
                            instance_id = int(component_parts[1])
                        else:
                            component_type = component
                    else:
                        component_type = component

                    status = params[component]
                    self.handle_notify_status(component_type, instance_id, status)
            elif method == "NotifyEvent":
                for e in params.get('events', []):
                    component = e.get('component', "")
                    component_type = None
                    instance_id = 0
                    if ':' in component:
                        component_parts = component.split(':')
                        if len(component_parts) == 2:
                            component_type = component_parts[0]
                            instance_id = int(component_parts[1])
                        else:
                            component_type = component
                    else:
                        component_type = component

                    e["name"] = e["event"]
                    del e["event"]
                    self.handle_notify_event(component_type, instance_id, e)

        return None

    def handle_notify_status(self, component_type, instance_id, status):
        """
        Default handler for NotifyStatus RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param status: Data for the notification.
        :return: None
        """

        component = self.get_component(component_type=component_type, comp_id=instance_id)
        if component:
            component.process_status(status)

    def handle_notify_event(self, component_type, instance_id, event):
        """
        Default handler for NotifyEvent RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param event: The event to handle.
        :return: None
        """

        component = self.get_component(component_type=component_type, comp_id=instance_id)
        if component:
            component.handle_notify_event(event)
        else:
            self.logger.warning("'{}': Unable to find component (component_type={}, comp_id={}) to pass event '{}' to!".format(self.device.name, component_type, instance_id, event["name"]))

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            self.get_config()
            for component in self.system_components.values():
                component.get_status()

    def check_for_update(self):
        """
        Execute the Shelly.CheckForUpdate RPC command.

        :return:
        """
        def _response(response, error=None):
            if error:
                self.logger.error(error)
                return

            if "stable" in response:
                stable_version = response["stable"].get("version", "Unknown")
                self.logger.info("Newer stable version ({}) found for {}".format(stable_version, self.device.name))

            if "beta" in response:
                beta_version = response["beta"].get("version", "Unknown")
                self.logger.info("Newer beta version ({}) found for {}".format(beta_version, self.device.name))

            if "stable" not in response and "beta" not in response:
                self.logger.info("{} is on the latest firmware".format(self.device.name))

        self.publish_rpc("Shelly.CheckForUpdate", callback=_response)

    def update(self, stage="stable"):
        """

        :return:
        """
        def _response(response, error=None):
            if error:
                self.logger.error(error)
                return

        self.publish_rpc("Shelly.Update", {"stage": stage}, callback=_response)
        self.logger.info("Updating {}...".format(self.device.name))
