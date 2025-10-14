# Example in connector_manager.py
from openscada_lite.modules.communication.drivers.test.marklin_driver import TrainTestDriver
from openscada_lite.modules.communication.drivers.driver_protocol import DriverProtocol
from openscada_lite.modules.communication.drivers.test.tank_test_driver import TankTestDriver
from openscada_lite.modules.communication.drivers.test.boiler_test_driver import BoilerTestDriver

DRIVER_REGISTRY = {
    "TankTestDriver": TankTestDriver,
    "BoilerTestDriver": BoilerTestDriver,
    "TrainTestDriver": TrainTestDriver
}