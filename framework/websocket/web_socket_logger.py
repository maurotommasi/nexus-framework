import sys
import asyncio

class WebSocketLogger:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    def write(self, message):
        # Ignore empty lines
        if message.strip():
            asyncio.create_task(self.queue.put(message.strip()))

    def flush(self):
        pass  # Required for file-like object
