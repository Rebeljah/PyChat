import asyncio
from collections import defaultdict
from inspect import iscoroutinefunction


class PubSub:
    def __init__(self):
        self.subscribers = defaultdict(set)

    def subscribe(self, trigger, callback):
        self.subscribers[trigger].add(callback)

    def publish(self, trigger,):
        """Publish the trigger event to subscribers."""

        event_type = trigger.__class__

        for callback in self.subscribers[event_type]:
            if iscoroutinefunction(callback):
                asyncio.create_task(callback(trigger))
            else:
                callback(trigger)
