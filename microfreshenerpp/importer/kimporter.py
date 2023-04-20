from abc import ABC, abstractmethod

from microfreshenerpp.kmodel.kube_cluster import KubeCluster


class KImporter(ABC):

    @abstractmethod
    def Import(self, path: str) -> KubeCluster:
        pass
