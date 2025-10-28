# -----------------------------------------------------------------------------
# Copyright 2025 Daniel Fernandez Boada
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
