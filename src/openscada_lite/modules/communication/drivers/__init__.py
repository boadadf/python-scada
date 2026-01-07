# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

# Example in connector_manager.py
from openscada_lite.modules.communication.drivers.test.test_camera import CameraDriver
from openscada_lite.modules.communication.drivers.test.stress_test_driver import (
    StressTestDriver,
)
from openscada_lite.modules.communication.drivers.test.marklin_driver import (
    TrainTestDriver,
)
from openscada_lite.modules.communication.drivers.opc_ua_server_driver import (
    OPCUAServerDriver,
)
from openscada_lite.modules.communication.drivers.test.tank_test_driver import (
    TankTestDriver,
)
from openscada_lite.modules.communication.drivers.test.boiler_test_driver import (
    BoilerTestDriver,
)

DRIVER_REGISTRY = {
    "TankTestDriver": TankTestDriver,
    "BoilerTestDriver": BoilerTestDriver,
    "TrainTestDriver": TrainTestDriver,
    "OPCUAServerDriver": OPCUAServerDriver,
    "StressTestDriver": StressTestDriver,
    "CameraDriver": CameraDriver,
}
