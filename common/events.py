import asyncio
from collections import defaultdict
from inspect import iscoroutinefunction


class Event:
    """Base class for events that can be emitted and subscribed to"""
    pass


class GuiSentMessage(Event):
    def __init__(self, text):
        self.text = text


class ReceivedMessage(Event):
    def __init__(self, message):
        self.message = message


class PubSub:
    def __init__(self):
        self.subscribers = defaultdict(set)

    def subscribe(self, trigger, callback):
        self.subscribers[trigger].add(callback)

    def publish(self, trigger, pass_attrs=True):
        """Publish the trigger event to subscribers. If pass_attrs is set
        to True, the __dict__ of the trigger is passed as kwargs to the
        callback, otherwise the trigger itself is passed"""

        kwargs = trigger.__dict__
        event_type = trigger.__class__

        for callback in self.subscribers[event_type]:
            if iscoroutinefunction(callback):
                if pass_attrs:
                    asyncio.create_task(callback(**kwargs))
                else:
                    asyncio.create_task(callback(trigger))
            else:
                if pass_attrs:
                    callback(**kwargs)
                else:
                    callback(trigger)

