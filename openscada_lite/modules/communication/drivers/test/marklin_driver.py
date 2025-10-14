# tank_test_driver.py
from openscada_lite.modules.communication.drivers.test.test_driver import TestDriver

class TrainTestDriver(TestDriver):
    async def _simulate_values(self):
        pass