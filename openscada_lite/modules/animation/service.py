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
from simpleeval import simple_eval
from typing import Union
from openscada_lite.common.models.entities import AnimationEntry
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import (
    AlarmUpdateMsg,
    AnimationUpdateMsg,
    AnimationUpdateRequestMsg,
    DriverConnectStatus,
    TagUpdateMsg,
)
from openscada_lite.common.config.config import Config
from .handlers.tag_handler import TagHandler
from .handlers.alarm_handler import AlarmHandler
from .handlers.connection_handler import ConnectionHandler


class AnimationService(
    BaseService[
        Union[TagUpdateMsg, AlarmUpdateMsg, DriverConnectStatus],
        AnimationUpdateRequestMsg,
        AnimationUpdateMsg,
    ]
):
    """
    Central animation orchestration service.
    Delegates to specialized handlers depending on the message type.
    """

    DURATION_DEFAULT = 0.5

    def __init__(self, event_bus, model, controller):
        super().__init__(
            event_bus,
            model,
            controller,
            [TagUpdateMsg, AlarmUpdateMsg, DriverConnectStatus],
            AnimationUpdateRequestMsg,
            AnimationUpdateMsg,
        )
        config = Config.get_instance()
        self.animations = config.get_animations()
        self.datapoint_map = config.get_animation_datapoint_map()

        # register handlers
        self.handlers = [
            TagHandler(),
            AlarmHandler(),
            ConnectionHandler(),
        ]

        # initialize default visuals
        self._init_animations_to_default()

    def _init_animations_to_default(self):
        """Initialize all animations in the model with their default values."""
        for dp_id, mappings in self.datapoint_map.items():
            for svg_name, elem_id, anim_name in mappings:
                animation = self.animations.get(anim_name)
                if not animation:
                    continue

                agg_attr = {}
                agg_text = None
                for entry in animation.entries:
                    if getattr(entry, "default", None) is None:
                        continue
                    if entry.attribute == "text":
                        agg_text = str(entry.default)
                    else:
                        agg_attr[entry.attribute] = entry.default

                cfg = {"attr": agg_attr, "duration": self.DURATION_DEFAULT}
                if agg_text:
                    cfg["text"] = agg_text

                self.model.update(
                    AnimationUpdateMsg(
                        svg_name=svg_name,
                        element_id=elem_id,
                        animation_type=anim_name,
                        value=None,
                        config=cfg,
                        test=False,
                    )
                )

    def process_msg(self, msg):
        """Delegate the processing to the appropriate handler."""
        for handler in self.handlers:
            if handler.can_handle(msg):
                return handler.handle(msg, self)
        return []

    async def handle_controller_message(self, data: AnimationUpdateRequestMsg):
        animations = self.process_msg(data.to_test_update_msg())
        for anim in animations:
            self.controller.publish(anim)

    def should_accept_update(self, msg) -> bool:
        # Accept TagUpdateMsg if there's a configured animation for that datapoint
        if isinstance(msg, TagUpdateMsg):
            return msg.datapoint_identifier in self.datapoint_map
        return True

    def process_single_entry(self, entry: AnimationEntry, value, quality):
        """
        Process a single AnimationEntry and return (attr_changes: dict, text: str or None, duration)
        """
        attr_changes = {}
        text_change = None
        duration = getattr(entry, "duration", self.DURATION_DEFAULT)

        expr = getattr(entry, "expression", None)
        fallback = (entry.quality or {}).get("unknown", None)

        # If a quality-based mapping exists and matches, prefer it
        evaluated = None
        if quality and getattr(entry, "quality", None) and quality in entry.quality:
            evaluated = entry.quality[quality]
        else:
            evaluated = self._evaluate_expression(expr, value, quality)

        if evaluated is None:
            evaluated = fallback

        if evaluated is not None and getattr(entry, "attribute", None):
            if entry.attribute == "text":
                text_change = str(evaluated)
            else:
                attr_changes[entry.attribute] = evaluated

        return attr_changes, text_change, duration

    async def schedule_revert(self, svg_name, element_id, animation_name, entry):
        """
        Revert a single animation entry to its configured default after entry.revertAfter seconds.
        The revert uses entry.default, not any quality logic.
        """
        delay = getattr(entry, "revertAfter", 0) or 0
        if delay <= 0:
            return
        await asyncio.sleep(delay)
        if (
            not hasattr(entry, "default")
            or entry.default is None
            or entry.default == ""
        ):
            return

        revert_cfg = {
            "attr": {},
            "duration": getattr(entry, "duration", self.DURATION_DEFAULT),
        }
        if entry.attribute == "text":
            revert_cfg["text"] = str(entry.default)
        else:
            revert_cfg["attr"][entry.attribute] = entry.default

        self.controller.publish(
            AnimationUpdateMsg(
                svg_name=svg_name,
                element_id=element_id,
                animation_type=animation_name,
                value=None,
                config=revert_cfg,
                test=False,
            )
        )

    def _evaluate_expression(self, expr, value, quality):
        """
        Evaluate expression.
        - if expr is dict, return expr.get(str(value))
        - if expr is string, evaluate with simple_eval (names={"value": value})
        """
        if isinstance(expr, dict):
            return expr.get(str(value))
        elif isinstance(expr, str):
            try:
                return simple_eval(expr, names={"value": value})
            except Exception as e:
                print(
                    f"AnimationService: error evaluating '{expr}' with value={value}: {e}"
                )
                return None
        return None
