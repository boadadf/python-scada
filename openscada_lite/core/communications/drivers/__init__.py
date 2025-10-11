# Example in connector_manager.py
from openscada_lite.core.communications.drivers.test.marklin_driver import TrainTestDriver
from openscada_lite.core.communications.drivers.driver_protocol import DriverProtocol
from openscada_lite.core.communications.drivers.test.tank_test_driver import TankTestDriver
from openscada_lite.core.communications.drivers.test.boiler_test_driver import BoilerTestDriver

DRIVER_REGISTRY = {
    "TankTestDriver": TankTestDriver,
    "BoilerTestDriver": BoilerTestDriver,
    "TrainTestDriver": TrainTestDriver
}