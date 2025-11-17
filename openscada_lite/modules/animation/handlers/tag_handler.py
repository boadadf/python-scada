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
from openscada_lite.common.models.dtos import TagUpdateMsg, AnimationUpdateMsg


class TagHandler:
    def can_handle(self, msg) -> bool:
        return isinstance(msg, TagUpdateMsg)

    def handle(self, msg, service):
        updates = []
        mappings = service.datapoint_map.get(msg.datapoint_identifier, [])
        if not mappings:
            return updates

        for svg_name, elem_id, anim_name in mappings:
            animation = service.animations.get(anim_name)
            if not animation:
                continue

            agg_attr = {}
            agg_text = None
            duration = service.DURATION_DEFAULT

            for entry in animation.entries:
                if getattr(entry, "triggerType", "datapoint") == "alarm":
                    continue

                attr_changes, text_change, dur = service.process_single_entry(
                    entry, msg.value, msg.quality
                )
                agg_attr.update(attr_changes)
                if text_change is not None:
                    agg_text = text_change
                duration = dur or duration

                if getattr(entry, "revertAfter", 0):
                    asyncio.create_task(
                        service.schedule_revert(svg_name, elem_id, anim_name, entry)
                    )

            cfg = {"attr": agg_attr, "duration": duration}
            if agg_text:
                cfg["text"] = agg_text

            updates.append(
                AnimationUpdateMsg(
                    svg_name=svg_name,
                    element_id=elem_id,
                    animation_type=anim_name,
                    value=msg.value,
                    config=cfg,
                    test=getattr(msg, "test", False),
                )
            )
        return updates
