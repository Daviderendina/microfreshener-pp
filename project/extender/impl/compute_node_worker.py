from microfreshener.core.model.nodes import Compute, Service

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import COMPUTE_NODE_WORKER
from project.ignorer.ignore_config import IgnoreConfig
from project.ignorer.ignore_nothing import IgnoreNothing


class ComputeNodeWorker(KubeWorker):

    def __init__(self):
        super().__init__(COMPUTE_NODE_WORKER)
        self.cluster = None
        self.model = None

    def refine(self, model, kube_cluster, ignore: IgnoreConfig):
        self.model = model
        self.cluster = kube_cluster

        not_ignored = self._get_nodes_not_ignored(list(self.model.services), ignore if ignore else IgnoreNothing)

        for workload in self.cluster.workloads:
            compute_node = self._get_or_create_compute(workload.typed_fullname)

            for container in workload.containers:
                container_node = self.model.get_node_by_name(container.typed_fullname, Service)

                if container_node and container_node in not_ignored:
                    model.add_deployed_on(container_node, compute_node)

    def _get_or_create_compute(self, compute_name):
        compute_node = self.model.get_node_by_name(compute_name, Compute)

        if compute_node is None:
            compute_node = Compute(compute_name)
            self.model.add_node(compute_node)

        return compute_node

    def _add_compute_node_if_not_present(self, compute_node: Compute):
        if compute_node not in self.model.computes:
            self.model.add_node(compute_node)
