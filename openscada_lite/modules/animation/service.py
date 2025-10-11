import asyncio
from typing import Union
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import AlarmUpdateMsg, AnimationUpdateMsg, AnimationUpdateRequestMsg, DriverConnectStatus, TagUpdateMsg
from openscada_lite.common.models.entities import Animation, AnimationEntry
from simpleeval import simple_eval


class AnimationService(BaseService[Union[TagUpdateMsg,AlarmUpdateMsg], AnimationUpdateRequestMsg, AnimationUpdateMsg]):
    """
    AnimationService processes datapoint updates and generates animation instructions for the SCADA frontend.

    - It loads animation rules from the configuration (see the "animations" section in system_config.json).
    - Each animation rule can specify an 'expression' field, which is either:
        * a string formula (e.g., "390 - ((value/100) * 340)") evaluated using the 'simpleeval' library,
        * or a dictionary mapping enum values to results (e.g., {"OPENED": "green", "CLOSED": "red"}).
    - When a TagUpdateMsg is received, the service:
        1. Looks up the animation config for the affected datapoint.
        2. Evaluates the expression(s) using the current value.
        3. Builds a GSAP-compatible config object for the frontend to animate SVG elements.

    Example supported animation config:
        "animations": {
            "fill_level": [
                {
                    "attribute": "y",
                    "quality": { "unknown": 390 },
                    "expression": "390 - ((value/100) * 340)"
                },
                {
                    "attribute": "height",
                    "quality": { "unknown": 0 },
                    "expression": "(value/100) * 340"
                }
            ],
            "toggle_opened_closed": [
                {
                    "attribute": "fill",
                    "quality": { "unknown": "gray" },
                    "expression": {
                        "OPENED": "green",
                        "CLOSED": "red"
                    }
                }
            ],
            "toggle_start_stop": [
                {
                    "attribute": "fill",
                    "quality": { "unknown": "gray" },
                    "expression": {
                        "STARTED": "green",
                        "STOPPED": "brown"
                    }
                }
            ],
            "level_text": [
                {
                    "attribute": "text",
                    "quality": { "unknown": "0.0" },
                    "expression": "str(value)"
                }
            ]
        }

    This allows flexible, safe, and dynamic SVG animation logic in the SCADA UI.
    """
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, [TagUpdateMsg, AlarmUpdateMsg], AnimationUpdateRequestMsg, AnimationUpdateMsg)
        config = Config.get_instance()
        self.animations = config.get_animations()
        # datapoint_map maps identifiers -> list of (svg_name, element_id, animation_name)
        self.datapoint_map = config.get_animation_datapoint_map()
        self.DURATION_DEFAULT = 0.5

    def should_accept_update(self, msg) -> bool:
        # Accept TagUpdateMsg if there's a configured animation for that datapoint
        if isinstance(msg, TagUpdateMsg):
            return msg.datapoint_identifier in self.datapoint_map
        # Accept all AlarmUpdateMsg (we filter by mapping entries later)
        if isinstance(msg, AlarmUpdateMsg):
            return True
        return False

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
                print(f"AnimationService: error evaluating '{expr}' with value={value}: {e}")
                return None
        return None

    def _process_single_entry(self, entry: AnimationEntry, value, quality):
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

    async def _schedule_revert(self, svg_name, element_id, animation_name, entry):
        """
        Revert a single animation entry to its configured default after entry.revertAfter seconds.
        The revert uses entry.default, not any quality logic.
        """
        delay = getattr(entry, "revertAfter", 0) or 0
        if delay <= 0:
            return
        await asyncio.sleep(delay)
        if not hasattr(entry, "default") or entry.default is None or entry.default == "":
            return

        revert_cfg = {"attr": {}, "duration": getattr(entry, "duration", self.DURATION_DEFAULT)}
        if entry.attribute == "text":
            revert_cfg["text"] = str(entry.default)
        else:
            revert_cfg["attr"][entry.attribute] = entry.default

        self.controller.publish(AnimationUpdateMsg(
            svg_name=svg_name,
            element_id=element_id,
            animation_type=animation_name,
            value=None,
            config=revert_cfg,
            test=False
        ))

    def process_msg(self, msg):
        """
        Unified processing for TagUpdateMsg and AlarmUpdateMsg.
        For alarms, we determine the event_name based on timestamps and trigger animations
        whose 'alarmEvent' matches that event.
        """
        updates = []
        identifier = getattr(msg, "datapoint_identifier", None) or getattr(msg, "alarm_id", None)
        if not identifier:
            return updates

        mappings = self.datapoint_map.get(identifier, [])
        if not mappings:
            return updates

        # --- TAG UPDATES ---
        if isinstance(msg, TagUpdateMsg):
            for svg_name, elem_id, anim_name in mappings:
                animation = self.animations.get(anim_name)
                if not animation:
                    continue

                agg_attr = {}
                agg_text = None
                duration = self.DURATION_DEFAULT

                for entry in animation.entries:
                    if getattr(entry, "triggerType", "datapoint") == "alarm":
                        continue

                    attr_changes, text_change, dur = self._process_single_entry(entry, msg.value, msg.quality)
                    agg_attr.update(attr_changes)
                    if text_change is not None:
                        agg_text = text_change
                    duration = dur or duration

                    if getattr(entry, "revertAfter", 0):
                        asyncio.create_task(self._schedule_revert(svg_name, elem_id, anim_name, entry))

                cfg = {"attr": agg_attr, "duration": duration}
                if agg_text is not None:
                    cfg["text"] = agg_text

                updates.append(AnimationUpdateMsg(
                    svg_name=svg_name,
                    element_id=elem_id,
                    animation_type=anim_name,
                    value=msg.value,
                    config=cfg,
                    test=getattr(msg, "test", False)
                ))

        # --- ALARM UPDATES ---
        elif isinstance(msg, AlarmUpdateMsg):
            print(f"Processing AlarmUpdateMsg: {msg} mappings {mappings}")

            # Determine the alarm event type from timestamps
            if msg.deactivation_time and msg.acknowledge_time and msg.activation_time:
                event_name = "FINISHED"
            elif msg.deactivation_time:
                event_name = "INACTIVE"
            elif msg.acknowledge_time:
                event_name = "ACK"
            elif msg.activation_time:
                event_name = "ACTIVE"
            else:
                event_name = "UNKNOWN"

            print(f"[AnimationService] Derived alarm event: {event_name}")

            for svg_name, elem_id, anim_name in mappings:
                animation = self.animations.get(anim_name)
                if not animation:
                    continue

                agg_attr = {}
                agg_text = None
                duration = self.DURATION_DEFAULT

                for entry in animation.entries:
                    if getattr(entry, "triggerType", "datapoint") != "alarm":
                        continue

                    entry_event = getattr(entry, "alarmEvent", "") or "onAlarmActive"

                    # Determine whether this animation entry should trigger
                    trigger_map = {
                        "onAlarmActive": event_name == "ACTIVE",
                        "onAlarmAck": event_name == "ACK",
                        "onAlarmInactive": event_name == "INACTIVE",
                        "onAlarmFinished": event_name == "FINISHED",
                    }

                    condition = trigger_map.get(entry_event, False)
                    value_key = "ACTIVE" if condition else "INACTIVE"

                    attr_changes, text_change, dur = self._process_single_entry(entry, value_key, getattr(msg, "quality", None))
                    agg_attr.update(attr_changes)
                    if text_change is not None:
                        agg_text = text_change
                    duration = dur or duration

                    if getattr(entry, "revertAfter", 0):
                        asyncio.create_task(self._schedule_revert(svg_name, elem_id, anim_name, entry))

            cfg = {"attr": agg_attr, "duration": duration}
            if agg_text is not None:
                cfg["text"] = agg_text

            print(f"AnimationService: Alarm {msg.datapoint_identifier} producing config {cfg}")

            updates.append(AnimationUpdateMsg(
                svg_name=svg_name,
                element_id=elem_id,
                animation_type=anim_name,
                value=None,
                config=cfg,
                test=getattr(msg, "test", False)
            ))

        return updates
    
