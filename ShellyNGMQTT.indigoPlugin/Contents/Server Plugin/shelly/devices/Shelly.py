import indigo
import json
import logging
import uuid


class Shelly(object):
    """

    """

    def __init__(self, device):
        """

        :param device: The indigo device
        """
        self.device = device
        self.components = []
        self.logger = logging.getLogger("Plugin.ShellyMQTT")
        self.rpc_callbacks = {}

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
            if component.device.id == device.id:
                return component
        return None

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

    def get_topics(self):
        return []

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

    def handle_message(self, topic, payload):
        """
        The default handler for incoming messages.
        These are messages that are handled by ANY Shelly device.

        :param topic: The topic of the incoming message.
        :param payload: The content of the massage.
        :return:  None
        """

        if topic == "{}/online".format(self.get_address()):
            self.device.updateStateOnServer(key='online', value=(payload == "true"))
            # TODO: state image?
            # self.update_state_image()
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

        pass

    def handle_notify_event(self, component_type, instance_id, event):
        """
        Default handler for NotifyEvent RPC messages.

        :param component_type: The component type.
        :param instance_id: The identifier of the component.
        :param event: The event to handle.
        :return: None
        """

        pass

    def handle_action(self, action):
        """
        The default handler for an action.

        :param action: The Indigo action to handle.
        :return: None
        """

        self.logger.info("{} - handle_action({})".format(self.device.name, action))
