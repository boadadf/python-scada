from openscada_lite.backend.rule.actioncommands.lower_alarm import LowerAlarmAction
from openscada_lite.backend.rule.actioncommands.raise_alarm import RaiseAlarmAction
from openscada_lite.backend.rule.actioncommands.send_command import SendCommandAction


ACTION_MAP = {
    "send_command": SendCommandAction(),
    "raise_alarm": RaiseAlarmAction(),
    "lower_alarm": LowerAlarmAction()
}