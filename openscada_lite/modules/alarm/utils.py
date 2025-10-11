from openscada_lite.modules.alarm.model import AlarmModel


class Utils:
    @staticmethod
    def get_latest_alarm(model: AlarmModel, rule_id: str):
        alarms = [
            alarm for alarm in model._store.values()
            if alarm.rule_id == rule_id
        ]
        if not alarms:
            return None
        return max(alarms, key=lambda a: a.activation_time)