from openscada_lite.common.config.config import Config
from openscada_lite.modules.animation.utils import Utils
from openscada_lite.modules.base.base_service import BaseService
from openscada_lite.common.models.dtos import AnimationUpdateMsg,TagUpdateMsg

class AnimationService(BaseService[TagUpdateMsg, None, AnimationUpdateMsg]):
    def __init__(self, event_bus, model, controller):
        super().__init__(event_bus, model, controller, TagUpdateMsg, None, AnimationUpdateMsg)
        config = Config.get_instance()
        self.animation_config = config.get_animation_config()
        self.datapoint_map = config.get_datapoint_map()

    def should_accept_update(self, msg: TagUpdateMsg) -> bool:
        return msg.datapoint_identifier in self.datapoint_map

    def process_msg(self, msg: TagUpdateMsg):
        updates = []
        for svg_name, elem_id, anim_type in self.datapoint_map.get(msg.datapoint_identifier, []):
            cfg = self.animation_config.get(anim_type, {})
            print(  f"Processing animation for {msg.datapoint_identifier} on {svg_name}:{elem_id} with {anim_type} and cfg {cfg}" )
            gsap_cfg = Utils.compute_gsap_cfg(cfg, msg.value)
            updates.append(AnimationUpdateMsg(
                svg_name=svg_name,
                element_id=elem_id,
                animation_type=anim_type,
                value=msg.value,
                config=gsap_cfg
            ))
        return updates

