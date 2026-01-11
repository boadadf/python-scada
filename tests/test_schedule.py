import pytest

from openscada_lite.modules.schedule.model import ScheduleModel
from openscada_lite.modules.schedule.service import ScheduleService
from openscada_lite.common.config.config import Config


class FakeScheduler:
    def __init__(self):
        self.jobs = []
        self.started = False

    def add_job(
        self, func, trigger, args=None, id=None, replace_existing=False, next_run_time=None
    ):
        self.jobs.append(
            {
                "func": func,
                "trigger": trigger,
                "args": args or [],
                "id": id,
                "replace_existing": replace_existing,
                "next_run_time": next_run_time,
            }
        )

    def start(self):
        self.started = True


class DummyEventBus:
    async def publish(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_schedule_registers_jobs_and_starts(monkeypatch):
    # Provide a dummy schedule config via Config
    class DummyConfig:
        def get_module_config(self, name):
            assert name == "schedule"
            return {
                "schedules": [
                    {"schedule_id": "on_mode", "cron": "*/5 * * * *", "actions": ["mode:on"]},
                    {"schedule_id": "off_mode", "cron": "0 23 * * *", "actions": ["mode:off"]},
                ]
            }

        @staticmethod
        def get_instance():
            return DummyConfig()

    # Monkeypatch Config.get_instance to our dummy
    monkeypatch.setattr(Config, "get_instance", DummyConfig.get_instance)
    # Monkeypatch AsyncIOScheduler to FakeScheduler
    import openscada_lite.modules.schedule.service as schedule_service_module

    monkeypatch.setattr(schedule_service_module, "AsyncIOScheduler", FakeScheduler)

    svc = ScheduleService(DummyEventBus(), ScheduleModel(), None)

    # Scheduler should be started
    assert isinstance(svc.scheduler, FakeScheduler)
    assert svc.scheduler.started is True

    # Two jobs should be registered
    assert len(svc.scheduler.jobs) == 2
    job_ids = {job["id"] for job in svc.scheduler.jobs}
    assert job_ids == {"on_mode", "off_mode"}

    # next_run_time should be set (immediate run behavior)
    assert all(job["next_run_time"] is not None for job in svc.scheduler.jobs)


@pytest.mark.asyncio
async def test_schedule_execute_triggers_actions(monkeypatch):
    # Dummy single schedule (parseable strings will be used below)

    # Capture execute_action calls (monkeypatch the symbol used in the schedule service module)
    calls = []

    async def fake_execute_action(action_str, identifier, track_id, rule_id):  # NOSONAR
        calls.append(
            {
                "action_str": action_str,
                "identifier": identifier,
                "track_id": track_id,
                "rule_id": rule_id,
            }
        )

    # Minimal service with fake scheduler
    import openscada_lite.modules.schedule.service as schedule_service_module

    monkeypatch.setattr(schedule_service_module, "AsyncIOScheduler", FakeScheduler)
    monkeypatch.setattr(schedule_service_module, "execute_action", fake_execute_action)
    svc = ScheduleService(DummyEventBus(), ScheduleModel(), None)

    # Execute directly
    # Use parseable action strings
    parseable_sched = {
        "schedule_id": "daily_toggle",
        "cron": "0 12 * * *",
        "actions": ["mode('toggle')", "notify('all')"],
    }
    await svc._execute_schedule(parseable_sched)

    # Verify actions executed in order
    assert [c["action_str"] for c in calls] == ["mode('toggle')", "notify('all')"]
    # Identifier should be SCHEDULER per implementation
    assert all(c["identifier"] == "SCHEDULER" for c in calls)
    # Rule id propagation
    assert all(c["rule_id"] == "daily_toggle" for c in calls)
    # Track id should be a UUID-like string (non-empty)
    assert all(isinstance(c["track_id"], str) and len(c["track_id"]) > 0 for c in calls)
