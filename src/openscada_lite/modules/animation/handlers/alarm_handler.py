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

import asyncio
from openscada_lite.common.models.dtos import AlarmUpdateMsg, AnimationUpdateMsg


class AlarmHandler:
    def can_handle(self, msg) -> bool:
        return isinstance(msg, AlarmUpdateMsg)

    def _determine_event_value(self, msg):
        """Determine current event based on timestamps."""
        if msg.deactivation_time and msg.acknowledge_time and msg.activation_time:
            return "FINISHED"
        elif msg.deactivation_time:
            return "INACTIVE"
        elif msg.acknowledge_time:
            return "ACK"
        elif msg.activation_time:
            return "ACTIVE"
        else:
            return "UNKNOWN"

    def _process_animation_entries(self, animation, event_value, quality, service):
        """Process animation entries and return aggregated attributes, text, and duration."""
        agg_attr, agg_text, duration = {}, None, service.DURATION_DEFAULT
        processed = False
        for entry in animation.entries:
            if getattr(entry, "trigger_type", "") != "alarm":
                continue
            processed = True
            attr_changes, text_change, dur = service.process_single_entry(
                entry, event_value, quality
            )
            agg_attr.update(attr_changes)
            if text_change:
                agg_text = text_change
            duration = dur or duration
        return processed, agg_attr, agg_text, duration

    def _schedule_revert_if_needed(self, entry, svg_name, elem_id, anim_name, service):
        if getattr(entry, "revert_after", 0):
            task = asyncio.create_task(
                service.schedule_revert(svg_name, elem_id, anim_name, entry)
            )
            task.add_done_callback(lambda t: t.exception())

    def handle(self, msg, service):
        updates = []
        identifier = getattr(msg, "datapoint_identifier", None) or getattr(
            msg, "alarm_id", None
        )
        if not identifier:
            return updates

        mappings = service.datapoint_map.get(identifier, [])
        if not mappings:
            return updates

        event_value = self._determine_event_value(msg)

        for svg_name, elem_id, anim_name in mappings:
            animation = service.animations.get(anim_name)
            if not animation:
                continue

            processed, agg_attr, agg_text, duration = self._process_animation_entries(
                animation, event_value, getattr(msg, "quality", None), service
            )

            if not processed:
                continue
            for entry in animation.entries:
                if getattr(entry, "trigger_type", "") == "alarm":
                    self._schedule_revert_if_needed(
                        entry, svg_name, elem_id, anim_name, service
                    )

            cfg = {"attr": agg_attr, "duration": duration}
            if agg_text:
                cfg["text"] = agg_text

            updates.append(
                AnimationUpdateMsg(
                    svg_name=svg_name,
                    element_id=elem_id,
                    animation_type=anim_name,
                    value=None,
                    config=cfg,
                    test=getattr(msg, "test", False),
                )
            )

        return updates
