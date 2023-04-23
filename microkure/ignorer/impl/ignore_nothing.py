from microkure.ignorer.impl.ignore_config import IgnoreType
from microkure.ignorer.ignorer import Ignorer


class IgnoreNothing(Ignorer):

    def is_ignored(self, node, check_type: IgnoreType, item_to_ignore: str):
        return False