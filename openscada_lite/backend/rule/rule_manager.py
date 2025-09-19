"""
Rule Engine module for evaluating and executing SCADA rules.

This module defines the RuleEngine class, which manages rule evaluation and action execution
based on tag updates. It supports rules with on/off conditions and actions, and maintains
the lifecycle state for each rule.
"""

import asyncio
import re
from asteval import Interpreter
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.config.config import Config
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.backend.rule.actioncommands.command_map import ACTION_MAP

class RuleEngine:
    """
    RuleEngine evaluates rules on tag updates and executes actions accordingly.

    - If a rule has both on_condition and off_condition, it follows an on/off lifecycle (actions are only triggered on state transitions).
    - If a rule has no off_condition, its on_actions are executed every time the on_condition is true (no latching).
    """

    def __init__(self, event_bus: EventBus):
        """
        Initialize the RuleEngine.

        Args:
            event_bus (EventBus): The event bus for subscribing to tag updates.
        """
        self.event_bus = event_bus
        self.asteval = Interpreter()
        self.rules = []
        self.datapoint_state = {}
        self.tag_to_rules = {}  # tag_id -> [rules]
        self.rule_states = {}   # rule_id -> bool (True=active, False=inactive)

    def _safe_key(self, tag_id):
        """Convert tag_id to a safe variable name for asteval."""
        return tag_id.replace("@", "__", 1)

    def load_rules(self):
        """
        Load rules from the configuration and build the tag-to-rules index.
        """
        config = Config.get_instance()
        self.rules = config.get_rules() or []
        self.build_tag_to_rules_index()

    def build_tag_to_rules_index(self):
        """
        Build a mapping from tag_id to the list of rules that reference it in their conditions.
        """
        self.tag_to_rules = {}
        tag_pattern = re.compile(r'([A-Za-z0-9]+@[A-Za-z0-9_]+)')
        for rule in self.rules:
            # Collect tags from on_condition and off_condition
            conditions = [rule.on_condition]
            if getattr(rule, "off_condition", None):
                conditions.append(rule.off_condition)
            for condition in conditions:
                tags = tag_pattern.findall(condition)
                for tag in tags:
                    self.tag_to_rules.setdefault(tag, []).append(rule)

    def subscribe_to_eventbus(self):
        """
        Subscribe the rule engine to tag update events on the event bus.
        """
        self.event_bus.subscribe(EventType.TAG_UPDATE, self.on_tag_update)

    async def on_tag_update(self, msg: TagUpdateMsg):
        """
        Callback for tag update events. Evaluates rules impacted by the tag and executes actions.

        - If a rule has no off_condition, its on_actions are always executed when on_condition is true.
        - If a rule has an off_condition, on_actions are only executed on transition from inactive to active, and off_actions on transition from active to inactive.

        Args:
            data (dict): The tag update event data, must include 'tag_id' and 'value'.
        """
        tag_id = msg.datapoint_identifier
        value = msg.value
        self.datapoint_state[tag_id] = value

        safe_key = self._safe_key(tag_id)
        self.asteval.symtable[safe_key] = value

        impacted_rules = self.tag_to_rules.get(tag_id, [])
        for rule in impacted_rules:
            rule_id = rule.rule_id
            on_active = self.rule_states.get(rule_id, False)
            try:
                on_result = self.asteval(rule.on_condition.replace("@", "__"))
                has_off = getattr(rule, "off_condition", None) is not None
                off_result = False
                if has_off:
                    off_result = self.asteval(rule.off_condition.replace("@", "__"))
            except Exception as e:
                print(f"[RuleEngine] Error evaluating rule {rule_id}: {e}")
                continue

            if has_off:
                # ON transition: only if not already active
                if not on_active and on_result:
                    self.rule_states[rule_id] = True
                    for action in getattr(rule, "on_actions", []):
                        await self.execute_action(action, tag_id, active=True)
                # OFF transition: only if currently active
                elif on_active and off_result:
                    self.rule_states[rule_id] = False
                    for action in getattr(rule, "off_actions", []):
                        await self.execute_action(action, tag_id, active=False)
            else:
                # No off_condition: always execute on_actions if on_condition is true (no latching)
                if on_result:
                    for action in getattr(rule, "on_actions", []):
                        await self.execute_action(action, tag_id, active=True)

    def parse_action(self, action_str):
        """
        Parse an action string into its name and parameters.

        Args:
            action_str (str): The action string, e.g., "raise_alarm('msg')".

        Returns:
            tuple: (action_name, params)
        """
        match = re.match(r"(\w+)\((.*)\)", action_str)
        if not match:
            raise ValueError(f"Invalid action string: {action_str}")
        action_name, params_str = match.groups()
        params = eval(f"({params_str},)") if params_str else ()
        return action_name, params

    async def execute_action(self, action_str, tag_id, active=True):
        """
        Execute an action by looking up its handler and calling it.

        Args:
            action_str (str): The action string to execute.
            tag_id (str): The tag that triggered the rule.
            active (bool): Whether this is an 'on' or 'off' action.
        """
        action_name, params = self.parse_action(action_str)
        handler = ACTION_MAP.get(action_name)
        if handler:
            # Pass self (engine), tag_id, params tuple
            await handler(self, tag_id, params)
        else:
            raise ValueError(f"Unknown action: {action_name}")
