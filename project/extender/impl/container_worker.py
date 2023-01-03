from microfreshener.core.model import Service

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import CONTAINER_WORKER, NAME_WORKER
from project.ignorer.impl.ignore_nothing import IgnoreNothing


class ContainerWorker(KubeWorker):

    def __init__(self):
        super().__init__(CONTAINER_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._check_for_edge_services(model, cluster, ignorer)
        return model

    def _check_for_edge_services(self, model, cluster, ignorer):
        not_ignored_services = self._get_nodes_not_ignored(model.services, ignorer)

        for workload in cluster.workloads:
            for container in workload.containers:
                service_node = model.get_node_by_name(container.typed_fullname, Service)

                if service_node and service_node in not_ignored_services:
                    to_expose = False

                    if workload.host_network:
                        to_expose = True
                    else:
                        for port in container.ports:
                            if port.get("host_port", None):
                                to_expose = True

                    if to_expose:
                        model.edge.add_member(service_node)
                    elif not to_expose and service_node in model.edge.members:
                        model.edge.remove_member(service_node)
