from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Service, Datastore, MessageRouter, Compute

from project.kmodel.istio import DestinationRule, Gateway, VirtualService
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kContainer import KContainer


class KubeWorker:
    # TODO devono avere un ordine di exec perché ad esempio quello dei service va fatto prima di quello di istio

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass


class IngressWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        pass
    # TODO controlla che
    #  i tool non si siano persi alcun Ingress per strada
    #  non si sia perso qualche IngressController (che viene segnato come MsgRouter)
    #  potrebbe anche sistemare il fatto delle relazioni
    # Sembra che il miner si preoccupi solo del controller, probabilmente perché le route le prende dinamicamente

    # Prima di aggiungere la risorsa, devo accertarmi che ci sia almeno un controller disponibile per gestirla, altrimenti ignoro tutto



class EdgeWorker(KubeWorker):
    pass
    # TODO effettua una serie di controlli per vedere che non ci siano Proxy, Endpoints, Entrypoint (?) e tutte ste cazzate
    # che espongano i nodi all'esterno ---> Non penso sia necessario


class MessageBrokerWorker(KubeWorker):
    pass
    # TODO non so se serve, controlla che non ci siano MSG broker in giro - non so se i può fare con le info che ho io a disposizione

