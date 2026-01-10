from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import uuid

from openscada_lite.common.actions.action_utils import execute_action
from openscada_lite.common.config.config import Config
from openscada_lite.modules.base.base_service import BaseService
import logging

logger = logging.getLogger(__name__)

class ScheduleService(BaseService[None, None, None]):
    def __init__(self, event_bus, model, controller):
        super().__init__(
            event_bus,
            model,
            controller,
            None,
            None,
            None
        )
        self.scheduler = AsyncIOScheduler()
        self.config = Config.get_instance()
        self.schedules = Config.get_instance().get_module_config("schedule").get("schedules", [])
        logger.debug(f"Loaded schedules: {self.schedules}")
        for sched in self.schedules:
            self._register_schedule(sched)
        self.scheduler.start()

    def _register_schedule(self, sched_cfg):
        trigger = CronTrigger.from_crontab(sched_cfg["cron"])
        self.scheduler.add_job(
            self._execute_schedule,
            trigger=trigger,
            args=[sched_cfg],
            id=sched_cfg["schedule_id"],
            replace_existing=True,
            next_run_time=datetime.now()
        )

    async def _execute_schedule(self, sched_cfg):
        track_id = str(uuid.uuid4())

        for action in sched_cfg.get("actions", []):
            await execute_action(
                action_str=action,
                identifier="SCHEDULER",
                track_id=track_id,
                rule_id=sched_cfg["schedule_id"],
            )

    def should_accept_update(self, msg: None) -> bool:
        return False
