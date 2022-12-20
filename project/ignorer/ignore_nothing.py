from project.ignorer.ignore_config import IgnoreType
from project.ignorer.ignorer import Ignorer


class IgnoreNothing(Ignorer):

    def is_node_ignored(self, node, check_type: IgnoreType, item_to_ignore: str):
        return False