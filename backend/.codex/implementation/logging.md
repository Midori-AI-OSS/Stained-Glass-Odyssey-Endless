# Logging

Battle modules and plugin packages should log through the shared backend logger.

```python
import logging

log = logging.getLogger(__name__)
```

Use `log.debug`, `log.info`, and so on instead of `print`. Records propagate through the queued buffer and are written to `backend/logs/backend.log` roughly every 15 seconds.

## Safe Shutdown

`request_shutdown()` flushes buffered log handlers before stopping the event
loop. Battle errors and unhandled exceptions call this helper automatically, but
it can also be imported and awaited manually during debugging to guarantee that
all log messages reach disk.

## High-Frequency Combat Logs

Combat loops enqueue messages via the `queue_log` helper in `rooms.battle`. A
background worker thread processes this queue and forwards entries to the
standard logger, ensuring combat iterations avoid synchronous I/O.

## Battle Modules

```python
from logging import getLogger

log = getLogger(__name__)

def attack(player, foe):
    log.info("%s attacks %s", player.name, foe.name)
    ...
```

## Plugins

```python
import logging

log = logging.getLogger(__name__)

class BurnRelic:
    plugin_type = "relic"
    id = "burn"

    def apply(self, target):
        log.debug("Applying burn to %s", target)
```
