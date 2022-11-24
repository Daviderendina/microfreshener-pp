from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel

from project.kmodel.kCluster import KCluster


class KubeWorker:

    def __init__(self):
        self.executed_only_after_workers = []

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass
