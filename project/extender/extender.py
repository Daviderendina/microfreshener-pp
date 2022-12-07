from abc import abstractmethod

from microfreshener.core.model.microtosca import MicroToscaModel
from typing import List

from project.extender.kubeworker import KubeWorker
from project.extender.workerimpl.compute_node_worker import ComputeNodeWorker
from project.extender.workerimpl.database_worker import DatabaseWorker
from project.extender.workerimpl.istio_worker import IstioWorker
from project.kmodel.kCluster import KCluster


class Extender:

    @abstractmethod
    def extend(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass


class KubeExtender(Extender):

    def __init__(self, worker_list: List[KubeWorker] = None):
        if worker_list is None:
            self.set_all_workers()
        else:
            self.worker_list: List[KubeWorker] = worker_list
        self._check_workers_order()

    def _check_workers_order(self):
        for i in range(0, len(self.worker_list)):
            worker = self.worker_list[i]
            for next_worker in self.worker_list[i+1:]:
                for worker_class in worker.executed_only_after_workers:
                    if isinstance(next_worker, worker_class):
                        raise AttributeError("Worker order does not respect execution constraints")

    def add_worker(self, worker: KubeWorker):
        self.worker_list.append(worker)

    def extend(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        extended_model = model
        for worker in self.worker_list:
            extended_model = worker.refine(model=model, kube_cluster=kube_cluster)
        return extended_model

    def set_all_workers(self):
        self.worker_list = [IstioWorker(), ComputeNodeWorker(), DatabaseWorker()]


