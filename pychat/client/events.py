from enum import Enum

from pychat.common.pubsub import PubSub


class GUIEvent(Enum):
    """Defines events that are emitted by the GUI"""
    pass


class ClientEvent(Enum):
    """Defines events that are emitted by the client"""
    pass


# pubsub used by GUI and client to communicate events
pubsub = PubSub()
