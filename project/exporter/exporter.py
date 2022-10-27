from abc import ABC, abstractmethod

from ..kmodel.kCluster import KCluster


class Exporter(ABC):

    @abstractmethod
    def export(self, cluster: KCluster):
        pass

