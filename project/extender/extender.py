from abc import abstractmethod

from microfreshener.core.model.microtosca import MicroToscaModel

from project.extender.kubeworker import KubeWorker, IstioWorker, ContainerWorker
from project.kmodel.kCluster import KCluster


class Extender:

    @abstractmethod
    def extend(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass


class KubeExtender(Extender):

    def __init__(self, worker_list: list[KubeWorker] = None):
        if worker_list is None:
            self.set_all_workers()
        else:
            self.worker_list: list[KubeWorker] = worker_list

    def add_worker(self, worker: KubeWorker):
        self.worker_list.append(worker)

    def extend(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        extended_model = model
        for worker in self.worker_list:
            extended_model = worker.refine(model=model, kubecluster=kube_cluster)
        return extended_model

    def set_all_workers(self):
        self.worker_list = [IstioWorker(), ContainerWorker()]


