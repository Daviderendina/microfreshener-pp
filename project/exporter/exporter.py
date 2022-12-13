from abc import ABC, abstractmethod

from project.kmodel.kube_cluster import KubeCluster


class Exporter(ABC):

    @abstractmethod
    def export(self, cluster: KubeCluster):
        pass

