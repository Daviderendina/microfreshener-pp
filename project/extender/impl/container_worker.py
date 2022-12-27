from microfreshener.core.model import MicroToscaModel, Service

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import CONTAINER_WORKER
from project.ignorer.ignore_config import IgnoreConfig
from project.kmodel.kube_cluster import KubeCluster


class ContainerWorker(KubeWorker):

    def __init__(self):
        super().__init__(CONTAINER_WORKER)
        self.model: MicroToscaModel = None
        self.cluster: KubeCluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig) -> MicroToscaModel:
        self.model = model
        self.cluster = kube_cluster

        self._check_for_edge_services(ignore)

    def _check_for_edge_services(self, ignore):
        for workload in self.cluster.workloads:
            not_ignored_services = self._get_nodes_not_ignored(self.model.services, ignore)

            for container in workload.containers:
                service_node = self.model.get_node_by_name(container.typed_fullname, Service)

                if service_node in not_ignored_services:
                    if workload.host_network:
                        self.model.edge.add_member(service_node)
                    else:
                        for port in container.ports:
                            if port.get("host_port", None):
                                self.model.edge.add_member(service_node)

