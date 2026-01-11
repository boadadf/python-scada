import re
from openscada_lite.common.actions.action_map import ACTION_MAP


def parse_action(action_str: str):
    """
    Parse an action string into its name and parameters.

    Args:
        action_str (str): The action string, e.g., "raise_alarm('msg')".

    Returns:
        tuple: (action_name, params)
    """
    match = re.match(r"(\w+)\((.*)\)", action_str, re.DOTALL)
    if not match:
        raise ValueError(f"Invalid action string: {action_str}")

    action_name, params_str = match.groups()
    params = eval(f"({params_str},)") if params_str else ()
    return action_name, params


async def execute_action(action_str, identifier, track_id, rule_id=None):
    """
    Execute an action by looking up its handler and calling it.

    Args:
        action_str (str): The action string to execute.
        identifier (str): The tag that triggered the rule.
        active (bool): Whether this is an 'on' or 'off' action.
        track_id (str): The track ID associated with the action.
    """
    action_name, params = parse_action(action_str)
    handler = ACTION_MAP.get(action_name)
    if not handler:
        raise ValueError(f"Unknown action: {action_name}")

    await handler(identifier, params, track_id=track_id, rule_id=rule_id)
