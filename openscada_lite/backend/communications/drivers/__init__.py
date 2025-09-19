# Example in connector_manager.py
from openscada_lite.backend.communications.drivers.driver_protocol import DriverProtocol
from openscada_lite.backend.communications.drivers.test.tank_test_driver import TankTestDriver
from openscada_lite.backend.communications.drivers.test.boiler_test_driver import BoilerTestDriver

DRIVER_REGISTRY = {
    "TankTestDriver": TankTestDriver,
    "BoilerTestDriver": BoilerTestDriver,
}