import indigo
import json
import logging
import uuid


class Shelly(object):
    """
    Base class used by all Shelly model classes.
    """

    display_name = "ShellyBase"

    def __init__(self, device):
        """Create a new Shelly device.

        :param device: The indigo device.
        """

        self.device = device
        self.functional_components = []
        self.system_components = {}
        self.component_devices = {}
        self.logger = logging.getLogger("Plugin.ShellyNGMQTT")
        self.rpc_callbacks = {}

        # Inspect devices in the group to find all components
        group_ids = indigo.device.getGroupList(self.device)
        for dev_id in group_ids:
            if dev_id != self.device.id:
                device = indigo.devices[dev_id]
                self.component_devices[device.model] = device

        self.device.updateStateImageOnServer(indigo.kStateImageSel.None)

    @property
    def components(self):
        """
        Getter for all functional and system components.

        :return: A list of all functional and system components.
        """

        return self.functional_components + self.system_components.values()

    def get_config(self):
        """
        Gets the config for all components

        :return: None
        """

        for component in self.components:
            component.get_config()

    #
    # Property getters
    #

    def get_address(self):
        """
        Helper function to get the base address of this device. Trailing '/' will be removed.

        :return: The cleaned base address.
        """

        address = self.device.pluginProps.get('address', None)
        if not address or address == '':
            return None

        address.strip()
        if address.endswith('/'):
            address = address[:-1]
        return address

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

    def get_component_for_device(self, device):
        """
        Utility to find a component that is associated with a specific indigo device.

        :param device:
        :return: Component
        """

        for component in self.components:
            if component.device and component.device.id == device.id:
                return component
        return None

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

        return [
            indigo.activePlugin.getDeviceStateDictForBoolYesNoType("online", "Online", "Online"),
            indigo.activePlugin.getDeviceStateDictForStringType("ip-address", "IP Address", "IP Address"),
            indigo.activePlugin.getDeviceStateDictForStringType("ssid", "Connected SSID", "Connected SSID"),
            indigo.activePlugin.getDeviceStateDictForNumberType("rssi", "WiFi Signal Strength (dBms)", "WiFi Signal Strength (dBms)"),
            indigo.activePlugin.getDeviceStateDictForStringType("mac-address", "Mac Address", "Mac Address"),
            indigo.activePlugin.getDeviceStateDictForNumberType("uptime", "Uptime (seconds)", "Uptime (seconds)"),
            indigo.activePlugin.getDeviceStateDictForStringType("available-firmware", "Available Firmware Version", "Available Firmware Version"),
            indigo.activePlugin.getDeviceStateDictForStringType("available-beta-firmware", "Available Beta Firmware Version", "Available Beta Firmware Version"),
        ]

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

    def publish_rpc(self, method, params, callback=None):
        """

        :return:
        """

        rpc_id = uuid.uuid4().hex
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

            if method == "NotifyStatus":
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

                    event = e.get('event', None)
                    self.handle_notify_event(component_type, instance_id, event)

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
            self.logger.warning("'{}': Unable to find component (component_type={}, comp_id={}) to pass event '{}' to!".format(self.device.name, component_type, instance_id, event))

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        if action.deviceAction == indigo.kDeviceAction.RequestStatus:
            for component in self.system_components.values():
                component.get_status()

    #
    # Utilities
    #

    def log_command_sent(self, message):
        """
        Helper method that logs when a device command is sent.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info("sent \"{}\" {}".format(self.device.name, message))

    def log_command_received(self, message):
        """
        Helper method that logs when a command is received.

        :param message: The message describing the command.
        :return: None
        """

        if indigo.activePlugin.pluginPrefs.get('log-device-activity', True):
            self.logger.info("received \"{}\" {}".format(self.device.name, message))

    def register_component(self, component_class, name, comp_id=0, props={}):
        """
        Find or create the Indigo device for the functional component.

        This is used for functional components that have their own Indigo
        devices. This just performs the association of an indigo device with a
        component object and the main shelly object.

        :param component_class: The class of the component to create.
        :param name: The name of the component (device model).
        :param comp_id: The identifier for the component.
        :param props: Properties to set for the device.
        :return: The created component object.
        """

        if props is None:
            props = {}
        if name not in self.component_devices:
            # The component name we are trying to register is new, so we did
            # not find a device with that name already in the group. Create it
            # and add it to the group.
            device = indigo.device.create(indigo.kProtocol.Plugin,
                                          deviceTypeId=component_class.device_type_id,
                                          groupWithDevice=self.device.id)
            device.model = name
            device.replaceOnServer()
            self.component_devices[name] = device

        device = self.component_devices.get(name, None)
        if device is None:
            raise KeyError("component '{}' not found in '{}' when it should...".format(name, self.device.name))

        # Force any device properties
        if len(props) > 0:
            device_props = device.pluginProps
            device_props.update(props)
            device.replacePluginPropsOnServer(device_props)
            device.stateListOrDisplayStateIdChanged()

        # Create the component
        component = component_class(self, device, comp_id)
        self.functional_components.append(component)
        return component

    def get_component(self, component_class=None, component_type=None, comp_id=0):
        """
        Utility to find the component object matching the criteria.

        :param component_class: Only return components that are an instance of this class.
        :param component_type: Only return components that have this type.
        :param comp_id: Only return components with this id.
        :return: The matching component.
        """

        for component in self.components:
            if component_class is not None and not isinstance(component, component_class):
                continue
            if component_type is not None and component.component_type != component_type:
                continue
            if component.comp_id != comp_id:
                continue
            # Made it this far, so all criteria matched
            return component
