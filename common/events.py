import asyncio
from collections import defaultdict
from inspect import iscoroutinefunction
from typing import Type


class Event:
    """Base class for events that can be emitted and subscribed to"""
    pass


class GUISentMessage(Event):
    def __init__(self, text):
        self.text = text


class PubSub:
    def __init__(self):
        self.subscribers = defaultdict(set)

    def subscribe(self, event_class: Type[Event], callback):
        self.subscribers[event_class].add(callback)

    def publish(self, event):
        for cb in self.subscribers[event.__class__]:
            if iscoroutinefunction(cb):
                asyncio.create_task(cb(**event.__dict__))
            else:
                cb(**event.__dict__)
