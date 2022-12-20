from microfreshener.core.model import MicroToscaModel

from project.constants import WorkerNames
from project.extender.kubeworker import KubeWorker
from project.ignorer.ignore_config import IgnoreConfig
from project.kmodel.kube_cluster import KubeCluster
from project.utils.utils import check_kobject_node_name_match


class ContainerWorker(KubeWorker):

    def __init__(self):
        super().__init__(WorkerNames.CONTAINER_WORKER)
        self.model: MicroToscaModel = None
        self.cluster: KubeCluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig) -> MicroToscaModel:
        self.model = model
        self.cluster = kube_cluster

        self._check_for_edge_services(ignore)

    def _check_for_edge_services(self, ignore):
        for workload in self.cluster.workloads:

            for container in workload.containers:
                not_ignored_services = self._get_nodes_not_ignored(self.model.services, ignore)
                service_nodes = [s for s in not_ignored_services if check_kobject_node_name_match(container, s)]

                if len(service_nodes) > 0:
                    service_node = service_nodes[0]
                    if workload.host_network:
                        self.model.edge.add_member(service_node)
                    else:
                        for port in container.ports:
                            if port.get("host_port", None):
                                self.model.edge.add_member(service_node)

