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

from openscada_lite.common.models.dtos import DriverConnectStatus, AnimationUpdateMsg

class ConnectionHandler:
    def can_handle(self, msg) -> bool:
        return isinstance(msg, DriverConnectStatus)

    def handle(self, msg, service):
        updates = []
        mappings = service.datapoint_map.get(msg.driver_name, [])
        if not mappings:
            return updates

        # Map driver status to a simple value
        event_value = "ONLINE" if msg.status.lower() == "online" else "OFFLINE"

        for svg_name, elem_id, anim_name in mappings:
            animation = service.animations.get(anim_name)
            if not animation:
                continue

            agg_attr, agg_text, duration = {}, None, service.DURATION_DEFAULT

            for entry in animation.entries:
                if getattr(entry, "triggerType", "") != "connection":
                    continue

                attr_changes, text_change, dur = service.process_single_entry(
                    entry, event_value, None
                )
                agg_attr.update(attr_changes)
                if text_change:
                    agg_text = text_change
                duration = dur or duration

            cfg = {"attr": agg_attr, "duration": duration}
            if agg_text:
                cfg["text"] = agg_text

            updates.append(AnimationUpdateMsg(
                svg_name=svg_name,
                element_id=elem_id,
                animation_type=anim_name,
                value=None,
                config=cfg,
                test=False
            ))

        return updates