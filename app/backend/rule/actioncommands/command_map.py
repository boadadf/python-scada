from backend.rule.actioncommands.lower_alarm import LowerAlarmAction
from backend.rule.actioncommands.raise_alarm import RaiseAlarmAction
from backend.rule.actioncommands.send_command import SendCommandAction


ACTION_MAP = {
    "send_command": SendCommandAction(),
    "raise_alarm": RaiseAlarmAction(),
    "lower_alarm": LowerAlarmAction()
}