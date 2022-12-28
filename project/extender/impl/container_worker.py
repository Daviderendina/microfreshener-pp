from microfreshener.core.model import MicroToscaModel, Service

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import CONTAINER_WORKER
from project.ignorer.ignore_nothing import IgnoreNothing


class ContainerWorker(KubeWorker):

    def __init__(self):
        super().__init__(CONTAINER_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._check_for_edge_services(model, cluster, ignorer)

        return model

    def _check_for_edge_services(self, model, cluster, ignorer):
        not_ignored_services = self._get_nodes_not_ignored(model.services, ignorer)

        for workload in cluster.workloads:
            for container in workload.containers:
                service_node = model.get_node_by_name(container.typed_fullname, Service)

                if service_node in not_ignored_services:
                    if workload.host_network:
                        model.edge.add_member(service_node)
                    else:
                        for port in container.ports:
                            if port.get("host_port", None):
                                model.edge.add_member(service_node)

