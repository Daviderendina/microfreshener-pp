from microfreshener.core.model import MicroToscaModel

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kobject_kind import KObjectKind


class ContainerWorker(KubeWorker):

    def __init__(self):
        super().__init__()
        self.model: MicroToscaModel = None
        self.kube_cluster: KCluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        self.model = model
        self.kube_cluster = kube_cluster

        self._check_for_edge_services()

    def _check_for_edge_services(self):
        for service in self.model.services:
            if not service in self.model.edge:
                for pod in self.kube_cluster.get_objects_by_kind(KObjectKind.POD):
                    if pod.spec.host_network == True:
                            self.model.edge.add_member(service)