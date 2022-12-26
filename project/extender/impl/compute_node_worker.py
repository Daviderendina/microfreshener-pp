from microfreshener.core.model.nodes import Compute

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import COMPUTE_NODE_WORKER
from project.ignorer.ignore_config import IgnoreConfig, IgnoreType
from project.ignorer.ignore_nothing import IgnoreNothing
from project.utils.utils import check_kobject_node_name_match


class ComputeNodeWorker(KubeWorker):

    def __init__(self):
        super().__init__(COMPUTE_NODE_WORKER)
        self.cluster = None
        self.model = None

    def refine(self, model, kube_cluster, ignore: IgnoreConfig):
        self.model = model
        self.cluster = kube_cluster

        if not ignore:
            ignore = IgnoreNothing()

        for container in self.cluster.containers:
            compute_node = self._get_or_create_compute(container.defining_workload_fullname)

            not_ignored_services = self._get_nodes_not_ignored(list(self.model.services), ignore)
            service_nodes = [s for s in not_ignored_services if check_kobject_node_name_match(container, s)]

            if len(service_nodes) > 0:
                self._add_compute_node_if_not_present(compute_node)
                model.add_deployed_on(source_node=service_nodes[0], target_node=compute_node)

    def _get_or_create_compute(self, compute_name):
        compute_node = self.model.get_node_by_name(compute_name)
        return compute_node if compute_node else Compute(compute_name)

    def _add_compute_node_if_not_present(self, compute_node: Compute):
        if compute_node not in self.model.computes:
            self.model.add_node(compute_node)



