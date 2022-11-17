from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel

from project.kmodel.kCluster import KCluster
from project.kmodel.kobject_kind import KObjectKind


class KubeWorker:

    def __init__(self):
        self.executed_only_after_workers = []

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass


class EdgeWorker(KubeWorker):
    pass
    # TODO effettua una serie di controlli per vedere che non ci siano Proxy, Endpoints, Entrypoint (?) e tutte ste cazzate
    # che espongano i nodi all'esterno ---> Non penso sia necessario


class MessageBrokerWorker(KubeWorker):
    pass
    # TODO non so se serve, controlla che non ci siano MSG broker in giro - non so se i può fare con le info che ho io a disposizione

