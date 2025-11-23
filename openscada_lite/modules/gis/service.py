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
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import AlarmUpdateMsg, GisUpdateMsg, TagUpdateMsg
from typing import Union


class GisService(BaseService[Union[TagUpdateMsg, AlarmUpdateMsg], None, GisUpdateMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(
            event_bus,
            model,
            controller,
            [TagUpdateMsg, AlarmUpdateMsg],
            None,
            GisUpdateMsg,
        )
        self.gis_icons_config = Config.get_instance().get_gis_icons()
        self.model = model

        # Initialize model with default icons
        for icon_cfg in self.gis_icons_config:
            gis_msg = GisUpdateMsg(
                id=icon_cfg["id"],
                latitude=icon_cfg["latitude"],
                longitude=icon_cfg["longitude"],
                icon=icon_cfg["icon"],
                label=icon_cfg.get("label"),
                navigation=icon_cfg.get("navigation"),
                navigation_type=icon_cfg.get("navigation_type"),
                extra={"datapoint-value": None},
            )
            print(f"Initializing GIS icon: {gis_msg}")
            self.model.update(gis_msg)

    def process_msg(self, msg: TagUpdateMsg | AlarmUpdateMsg) -> GisUpdateMsg | None:
        print(f"=================================GisService processing message: {msg}")
        for icon_cfg in self.gis_icons_config:
            # Handle TagUpdateMsg (datapoint-based icon state)
            if (
                isinstance(msg, TagUpdateMsg)
                and icon_cfg.get("datapoint") == msg.datapoint_identifier
            ):
                icon_url = icon_cfg["icon"]
                if "states" in icon_cfg and str(msg.value) in icon_cfg["states"]:
                    icon_url = icon_cfg["states"][str(msg.value)]
                gis_msg = GisUpdateMsg(
                    id=icon_cfg["id"],
                    latitude=icon_cfg["latitude"],
                    longitude=icon_cfg["longitude"],
                    icon=icon_url,
                    label=icon_cfg.get("label"),
                    navigation=icon_cfg.get("navigation"),
                    navigation_type=icon_cfg.get("navigation_type"),
                    extra={"datapoint-value": icon_url},
                )
                return gis_msg

            # Handle AlarmUpdateMsg (alarm-based icon state, match by rule_id)
            if isinstance(msg, AlarmUpdateMsg) and icon_cfg.get("rule_id") == getattr(
                msg, "rule_id", None
            ):

                # Determine alarm state
                if msg.deactivation_time and msg.acknowledge_time and msg.activation_time:
                    alarm_state = "FINISHED"
                elif msg.deactivation_time:
                    alarm_state = "INACTIVE"
                elif msg.acknowledge_time:
                    alarm_state = "ACK"
                elif msg.activation_time:
                    alarm_state = "ACTIVE"
                else:
                    alarm_state = "UNKNOWN"

                gis_msg = self.model.get(icon_cfg["id"])

                icon_url = icon_cfg["icon"]
                if "alarm" in icon_cfg and alarm_state in icon_cfg["alarm"]:
                    icon_url = icon_cfg["alarm"][alarm_state]
                    gis_msg.icon = icon_url
                else:
                    gis_msg.icon = gis_msg.extra.get("datapoint-value", gis_msg.icon)

                return gis_msg
        return None

    def should_accept_update(self, tag: Union[TagUpdateMsg, AlarmUpdateMsg]) -> bool:
        if isinstance(tag, AlarmUpdateMsg):
            return any(
                icon.get("rule_id") == getattr(tag, "rule_id", None)
                for icon in self.gis_icons_config
            )
        else:
            return any(
                icon.get("datapoint") == tag.datapoint_identifier for icon in self.gis_icons_config
            )
