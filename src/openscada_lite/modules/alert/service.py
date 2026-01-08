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

# communications_service.py
from openscada_lite.modules.alert.controller import AlertController
from openscada_lite.common.tracking.decorators import publish_from_arg_async
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.modules.alert.model import AlertModel
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import (
    ClientAlertMsg,
    ClientAlertFeedbackMsg,
    SendCommandMsg,
)


class AlertService(BaseService[ClientAlertMsg, ClientAlertFeedbackMsg, ClientAlertMsg]):
    def __init__(self, event_bus, model: AlertModel, controller: AlertController):
        super().__init__(
            event_bus,
            model,
            controller,
            ClientAlertMsg,
            ClientAlertFeedbackMsg,
            ClientAlertMsg,
        )

    def should_accept_update(self, msg: ClientAlertMsg) -> bool:
        return True

    @publish_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def handle_controller_message(self, data: ClientAlertFeedbackMsg):
        # Remove the ClientAlertMsg with the same get_id
        alert_id = data.get_id()
        alert_msg = self.model._store.pop(alert_id, None)

        # If it was stored (confirm_cancel), publish ClientAlertMsg with show=False
        if alert_msg and getattr(alert_msg, "alert_type", None) == "confirm_cancel":
            hide_msg = ClientAlertMsg(**{**alert_msg.__dict__, "show": False})
            self.controller.publish(hide_msg)
            if getattr(data, "feedback", None) == "confirm":
                # If command info present, send command to bus
                if getattr(alert_msg, "command_datapoint", None) and getattr(
                    alert_msg, "command_value", None
                ):
                    cmd_msg = SendCommandMsg(
                        command_id=data.get_id(),
                        datapoint_identifier=alert_msg.command_datapoint,
                        value=alert_msg.command_value,
                    )
                    await self.event_bus.publish(
                        SendCommandMsg.get_event_type(), cmd_msg
                    )
