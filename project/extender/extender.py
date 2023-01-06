from abc import abstractmethod

from microfreshener.core.model.microtosca import MicroToscaModel

from project.extender.impl.istio_circuit_breaker_worker import IstioCircuitBreakerWorker
from project.extender.impl.istio_gateway_worker import IstioGatewayWorker
from project.extender.impl.istio_timeout_worker import IstioTimeoutWorker
from project.extender.impl.message_router_edge_worker import MessageRouterEdgeWorker
from project.extender.impl.name_worker import NameWorker
from project.extender.impl.compute_node_worker import ComputeNodeWorker
from project.extender.impl.container_worker import ContainerWorker
from project.extender.impl.database_worker import DatabaseWorker
from project.extender.impl.ingress_worker import IngressWorker
from project.extender.impl.service_worker import ServiceWorker
from project.extender.worker_names import *
from project.ignorer.ignorer import Ignorer
from project.ignorer.impl.ignore_nothing import IgnoreNothing
from project.kmodel.kube_cluster import KubeCluster


class Extender:

    @abstractmethod
    def extend(self, model: MicroToscaModel, cluster: KubeCluster, ignore: Ignorer) -> MicroToscaModel:
        pass


class KubeExtender(Extender):

    WORKER_MAPPING = {
        NAME_WORKER: NameWorker(),
        CONTAINER_WORKER: ContainerWorker(),
        SERVICE_WORKER: ServiceWorker(),
        MESSAGE_ROUTER_EDGE_WORKER: MessageRouterEdgeWorker(),
        INGRESS_WORKER: IngressWorker(),
        ISTIO_GATEWAY_WORKER: IstioGatewayWorker(),
        ISTIO_TIMEOUT_WORKER: IstioTimeoutWorker(),
        ISTIO_CIRCUIT_BREAKER: IstioCircuitBreakerWorker(),
        COMPUTE_NODE_WORKER: ComputeNodeWorker(),
        DATABASE_WORKER: DatabaseWorker()
    }

    def __init__(self, worker_names_list=None):
        self.worker_list = []

        if worker_names_list is None:
            self.set_all_workers()
        else:
            for worker_name in worker_names_list:
                self.add_worker(worker_name)
        self._check_workers_order()

    @property
    def name_mapping(self):
        name_worker = [w for w in self.worker_list if w.name == NAME_WORKER]
        return name_worker[0].name_mapping if name_worker else {}

    def _check_workers_order(self):
        for i in range(0, len(self.worker_list)):
            worker = self.worker_list[i]
            for next_worker in self.worker_list[i+1:]:
                for worker_name in worker.executed_only_after_workers:
                    if worker_name == next_worker.name:
                        raise AttributeError(f"Worker order does not respect execution constraints: executing worker '{worker.name}' before worker '{worker_name}'")

    def add_worker(self, worker_name: str):
        worker = self.WORKER_MAPPING.get(worker_name, None)
        if worker:
            self.worker_list.append(worker)

    def extend(self, model: MicroToscaModel, cluster: KubeCluster, ignorer=IgnoreNothing()) -> MicroToscaModel:
        extended_model = model
        for worker in self.worker_list:
            extended_model = worker.refine(model, cluster, ignorer)
        return extended_model

    def set_all_workers(self, exclude: list = []):
        self.worker_list = [w for w in self.WORKER_MAPPING.values() if w.name not in exclude]


