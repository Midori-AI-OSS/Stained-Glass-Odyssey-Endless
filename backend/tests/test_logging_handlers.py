import logging
import queue

from battle_logging.handlers import AsyncQueueListener
from battle_logging.handlers import TimedMemoryHandler


def test_handlers_initialize(tmp_path):
    file_handler = logging.FileHandler(tmp_path / "test.log")
    handler = TimedMemoryHandler(file_handler, flush_interval=0.01)
    listener = AsyncQueueListener(queue.SimpleQueue(), handler)
    listener.start()
    handler.close()
