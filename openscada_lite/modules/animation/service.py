from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import AnimationUpdateMsg, TagUpdateMsg
from simpleeval import simple_eval


class AnimationService(BaseService[TagUpdateMsg, None, AnimationUpdateMsg]):
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
        super().__init__(event_bus, model, controller, TagUpdateMsg, None, AnimationUpdateMsg)
        config = Config.get_instance()
        self.animation_config = config.get_animation_config()
        self.datapoint_map = config.get_datapoint_map()
        self.DURATION_DEFAULT = 0.5

    def should_accept_update(self, msg: TagUpdateMsg) -> bool:
        return msg.datapoint_identifier in self.datapoint_map

    def _evaluate_expression(self, expr, value):
        """
        Evaluate an expression: either a dict (enum mapping) or a formula string.
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

    def _process_config(self, cfg, value):
        """
        Build GSAP config object {"attr": {...}, "duration": x}
        based on animation config and datapoint value.
        """
        result = {"attr": {}, "duration": self.DURATION_DEFAULT}
        rules = cfg if isinstance(cfg, list) else [cfg]

        for rule in rules:
            attribute = rule.get("attribute")
            expr = rule.get("expression")
            fallback = rule.get("quality", {}).get("unknown")

            evaluated = self._evaluate_expression(expr, value)
            if evaluated is None:
                evaluated = fallback
                    
            if attribute and evaluated is not None:
                if attribute == "text":
                    result["text"] = str(evaluated) if evaluated is not None else ""
                else:
                    result["attr"][attribute] = evaluated

        return result

    def process_msg(self, msg: TagUpdateMsg):
        updates = []
        for svg_name, elem_id, anim_type in self.datapoint_map.get(msg.datapoint_identifier, []):
            cfg = self.animation_config.get(anim_type, {})
            print(f"[AnimationService] Processing {msg.datapoint_identifier} → "
                  f"{svg_name}:{elem_id}, anim={anim_type}, cfg={cfg}")

            gsap_cfg = self._process_config(cfg, msg.value)

            updates.append(AnimationUpdateMsg(
                svg_name=svg_name,
                element_id=elem_id,
                animation_type=anim_type,
                value=msg.value,
                config=gsap_cfg
            ))
        print(f"[AnimationService] Generated updates: {updates}")
        return updates
