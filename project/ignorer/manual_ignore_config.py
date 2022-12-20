from project.ignorer.ignore_config import IgnoreConfig


class ManualIgnoreConfig(IgnoreConfig):

    def __init__(self):
        self.config = {
            "rules": []
        }
        self.schema = None

    def add_rule(self, node_name, node_tosca_type, ignore_type, ignored_item):
        for rule in self.config["rules"]:
            if rule["node"]["name"] == node_name and rule["node"]["type"] == node_tosca_type:
                if rule.get(ignore_type.value) is None:
                    rule[ignore_type.value] = []
                rule[ignore_type.value] = [ignored_item]
                return

        self.config["rules"].append(
            {
                "node": {
                    "name": node_name,
                    "type": node_tosca_type
                },
                ignore_type.value: [ignored_item]
            }
        )