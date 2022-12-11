from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel

from project.kmodel.kube_cluster import KubeCluster


class KubeWorker:

    def __init__(self):
        self.executed_only_after_workers = []

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster) -> MicroToscaModel:
        pass
