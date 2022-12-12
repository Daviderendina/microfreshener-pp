from microfreshener.core.model import MicroToscaModel

from project.extender.kubeworker import KubeWorker
from project.kmodel.kube_cluster import KubeCluster
from project.utils import check_kobject_node_name_match


class ContainerWorker(KubeWorker):

    def __init__(self):
        super().__init__()
        self.model: MicroToscaModel = None
        self.cluster: KubeCluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster) -> MicroToscaModel:
        self.model = model
        self.cluster = kube_cluster

        self._check_for_edge_services()

    def _check_for_edge_services(self):
        for workload in self.cluster.workloads:
            for container in workload.get_containers():
                service_nodes = [s for s in self.model.services if
                                 check_kobject_node_name_match(container, s, workload.fullname)]

                if len(service_nodes) > 0:
                    service_node = service_nodes[0]
                    if workload.is_host_network():
                        self.model.edge.add_member(service_node)
                    else:
                        for port in container.get_ports():
                            if port.get("host_port", None):
                                self.model.edge.add_member(service_node)

