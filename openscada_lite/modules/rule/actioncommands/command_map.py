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

from typing import Dict
from openscada_lite.modules.rule.actioncommands.action import Action
from openscada_lite.modules.rule.actioncommands.lower_alarm import LowerAlarmAction
from openscada_lite.modules.rule.actioncommands.raise_alarm import RaiseAlarmAction
from openscada_lite.modules.rule.actioncommands.send_command import SendCommandAction
from openscada_lite.modules.rule.actioncommands.client_alert import ClientAlertAction


ACTION_MAP: Dict[str, Action] = {
    "send_command": SendCommandAction(),
    "raise_alarm": RaiseAlarmAction(),
    "lower_alarm": LowerAlarmAction(),
    "client_alert": ClientAlertAction()
}