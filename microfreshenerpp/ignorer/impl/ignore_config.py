import json
import os.path

import jsonschema
from jsonschema.validators import validate
from microfreshener.core.model import Service, Compute, Datastore, MessageRouter, MessageBroker
from microfreshener.core.model.type import MICROTOSCA_NODES_SERVICE, MICROTOSCA_NODES_COMPUTE, \
    MICROTOSCA_NODES_MESSAGE_BROKER, MICROTOSCA_NODES_MESSAGE_ROUTER, MICROTOSCA_NODES_DATABASE

from microfreshenerpp.ignorer.ignorer import Ignorer, IgnoreType


class IgnoreConfig(Ignorer):

    def __init__(self, config_filepath: str, schema_filepath: str):

        if not os.path.exists(config_filepath):
            raise FileNotFoundError(f"File {config_filepath} not found")

        if not os.path.exists(schema_filepath):
            raise FileNotFoundError(f"File {schema_filepath} not found")

        config_file = open(config_filepath)
        schema_file = open(schema_filepath)

        self.config = json.load(config_file)
        self.schema = json.load(schema_file)

    def import_config(self):

        if not self.validate_json(self.config, self.schema):
            raise ValueError(f"Json config ({self.config}) is not valid")

    def is_ignored(self, node, check_type: IgnoreType, item_to_ignore: str):
        mapping = {
            MICROTOSCA_NODES_SERVICE: Service,
            MICROTOSCA_NODES_COMPUTE: Compute,
            MICROTOSCA_NODES_DATABASE: Datastore,
            MICROTOSCA_NODES_MESSAGE_BROKER: MessageBroker,
            MICROTOSCA_NODES_MESSAGE_ROUTER: MessageRouter
        }

        for rule in self.config["rules"]:
            rule_type = rule["node"]["type"]
            rule_name = rule["node"]["name"]

            if node.name == rule_name and isinstance(node, mapping.get(rule_type, None)):
                rules_to_check = rule.get(check_type.value, [])

                if "all" in rules_to_check or item_to_ignore in rules_to_check:
                    return True

        return False

    def validate_json(self, data, schema):
        try:
            validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as err:
            return False
        return True

    def adjust_names(self, name_worker_mapping: dict):
        for new_name, old_name in name_worker_mapping.items():
            for rule in self.config.get("rules", []):
                if rule.get("node", {}).get("name", "") == old_name:
                    rule["node"]["name"] = new_name