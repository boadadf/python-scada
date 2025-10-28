import asyncio
import datetime
from openscada_lite.modules.communication.drivers.test.test_driver import TestDriver

class StressTestDriver(TestDriver):
    async def _simulate_values(self):
        """
        Sequentially toggle all datapoints TRUE/FALSE with a delay.
        """
        now = datetime.datetime.now()
        for tag in self._tags.values():
            if not tag.datapoint_identifier.endswith("TEST"):
                tag.value = "TRUE" if tag.value == "FALSE" else "FALSE"
                tag.timestamp = now
