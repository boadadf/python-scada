# -----------------------------------------------------------------------------
# Copyright 2025 Daniel&Hector Fernandez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

"""
Rule Engine module for evaluating and executing SCADA rules.

This module defines the RuleEngine class, which manages rule evaluation and action execution
based on tag updates. It supports rules with on/off conditions and actions, and maintains
the lifecycle state for each rule.
"""

import re
from asteval import Interpreter
from openscada_lite.common.tracking.decorators import publish_data_flow_from_arg_async
from openscada_lite.modules.rule.actioncommands.action import Action
from openscada_lite.common.tracking.tracking_types import DataFlowStatus
from openscada_lite.common.bus.event_types import EventType
from openscada_lite.common.config.config import Config
from openscada_lite.common.bus.event_bus import EventBus
from openscada_lite.common.models.dtos import TagUpdateMsg
from openscada_lite.modules.rule.actioncommands.command_map import ACTION_MAP


class RuleEngine:
    """
    RuleEngine evaluates rules on tag updates and executes actions accordingly.

    - If a rule has both on_condition and off_condition, it follows an
      on/off lifecycle (actions are only triggered on state transitions).
    - If a rule has no off_condition, its on_actions are executed every time
      the on_condition is true (no latching).
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is not None:
            raise RuntimeError("Use RuleManager.get_instance() instead of direct instantiation.")
        cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    @classmethod
    def get_instance(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance

    def __init__(self, event_bus: EventBus = None):
        """
        Initialize the RuleEngine.

        Args:
            event_bus (EventBus): The event bus for subscribing to tag updates.
        """
        self.event_bus = event_bus if event_bus is not None else EventBus.get_instance()
        self.asteval = Interpreter()
        self.asteval.symtable["TRUE"] = True
        self.asteval.symtable["FALSE"] = False
        self.rules = []
        self.datapoint_state = {}
        self.tag_to_rules = {}  # tag_id -> [rules]
        self.rule_states = {}  # rule_id -> bool (True=active, False=inactive)
        self.load_rules()
        self.build_tag_to_rules_index()
        self.subscribe_to_eventbus()

    def _safe_key(self, tag_id):
        """Convert tag_id to a safe variable name for asteval."""
        return tag_id.replace("@", "__", 1)

    def load_rules(self):
        """
        Load rules from the configuration and build the tag-to-rules index.
        """
        config = Config.get_instance()
        self.rules = config.get_rules() or []

    def build_tag_to_rules_index(self):
        """
        Build mapping from tags (like Train@var) to rules that depend on them.
        This ensures both on/off conditions are considered.
        """
        self.tag_to_rules.clear()
        tag_pattern = re.compile(r"[A-Za-z0-9_]+@[A-Za-z0-9_]+")
        all_tags = set()
        for rule in self.rules:
            conditions = [rule.on_condition]
            if getattr(rule, "off_condition", None):
                conditions.append(rule.off_condition)

            for condition in conditions:
                for tag in tag_pattern.findall(condition or ""):
                    self.tag_to_rules.setdefault(tag, []).append(rule)
                    all_tags.add(tag)
        # Initialize all tags in asteval symtable
        for tag in all_tags:
            safe_key = self._safe_key(tag)
            if safe_key not in self.asteval.symtable:
                self.asteval.symtable[safe_key] = None

    def subscribe_to_eventbus(self):
        """
        Subscribe the rule engine to tag update events on the event bus.
        """
        self.event_bus.subscribe(EventType.TAG_UPDATE, self.on_tag_update)

    @publish_data_flow_from_arg_async(status=DataFlowStatus.RECEIVED)
    async def on_tag_update(self, msg: TagUpdateMsg):
        """
        Callback for tag update events. Evaluates rules impacted by the tag and executes actions.
        """
        tag_id = msg.datapoint_identifier
        value = msg.value
        self.datapoint_state[tag_id] = value

        safe_key = self._safe_key(tag_id)
        # Normalize string values to boolean only if they are "TRUE" or "FALSE"
        if isinstance(value, str) and value.upper() in ("TRUE", "FALSE"):
            self.asteval.symtable[safe_key] = value.upper() == "TRUE"
        else:
            self.asteval.symtable[safe_key] = value

        impacted_rules = self.tag_to_rules.get(tag_id, [])
        print(f"[RuleEngine] Received tag update: {tag_id} = {value}")
        print(
            f"[RuleEngine] Updated asteval "
            f"symbol table: {safe_key} = {self.asteval.symtable[safe_key]}"
        )
        print(f"[RuleEngine] Impacted rules: {impacted_rules}")
        for rule in impacted_rules:
            rule_id = rule.rule_id
            on_active = self.rule_states.get(rule_id, False)
            try:
                on_result = self.asteval(rule.on_condition.replace("@", "__"))
                print(f"[RuleEngine] Evaluated on_condition for rule {rule_id}: {on_result}")
                if self.asteval.error:
                    print("asteval errors:", self.asteval.error)
                off_cond = getattr(rule, "off_condition", None)
                has_off = bool(off_cond and off_cond.strip())
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
                        await self.execute_action(
                            action, tag_id, msg.track_id, active=True, rule_id=rule_id
                        )
                # OFF transition: only if currently active
                elif on_active and off_result:
                    self.rule_states[rule_id] = False
                    for action in getattr(rule, "off_actions", []):
                        await self.execute_action(
                            action, tag_id, msg.track_id, active=False, rule_id=rule_id
                        )
            else:
                # Only trigger on rising edge (transition from false to true)
                prev_active = self.rule_states.get(rule_id, False)
                if not prev_active and on_result:
                    self.rule_states[rule_id] = True
                    for action in getattr(rule, "on_actions", []):
                        await self.execute_action(
                            action, tag_id, msg.track_id, active=True, rule_id=rule_id
                        )
                elif prev_active and not on_result:
                    # Reset state so next true will trigger again
                    self.rule_states[rule_id] = False
                    # If raise_alarm is in on_actions, trigger lower_alarm automatically
                    if any("raise_alarm" in action for action in getattr(rule, "on_actions", [])):
                        await self.execute_action(
                            "lower_alarm()",
                            tag_id,
                            msg.track_id,
                            active=False,
                            rule_id=rule_id,
                        )

    def parse_action(self, action_str):
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

    async def execute_action(self, action_str, identifier, track_id, active=True, rule_id=None):
        """
        Execute an action by looking up its handler and calling it.

        Args:
            action_str (str): The action string to execute.
            identifier (str): The tag that triggered the rule.
            active (bool): Whether this is an 'on' or 'off' action.
            track_id (str): The track ID associated with the action.
        """
        action_name, params = self.parse_action(action_str)
        handler: Action = ACTION_MAP.get(action_name)
        if handler:
            # Pass self (engine), identifier, params tuple
            await handler(identifier, params, track_id=track_id, rule_id=rule_id)
        else:
            raise ValueError(f"Unknown action: {action_name}")
