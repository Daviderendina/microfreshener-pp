from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel

from project.kmodel.kCluster import KCluster


class KubeWorker:
    # TODO devono avere un ordine di exec perché ad esempio quello dei service va fatto prima di quello di istio

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

