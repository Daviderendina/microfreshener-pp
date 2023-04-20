from abc import abstractmethod
from enum import Enum


class IgnoreType(Enum):
    SMELLS = "ignore_smell"
    WORKER = "ignore_worker"
    REFACTORING = "ignore_refactoring"


class Ignorer:

    @abstractmethod
    def is_ignored(self, node, check_type: IgnoreType, item_to_ignore: str):
        pass
