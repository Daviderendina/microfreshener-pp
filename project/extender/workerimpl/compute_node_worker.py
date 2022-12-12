from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute

from project.extender.kubeworker import KubeWorker
from project.kmodel.kube_cluster import KubeCluster
from project.utils.utils import check_kobject_node_name_match


class ComputeNodeWorker(KubeWorker):

    def __init__(self):
        super().__init__()
        self.cluster = None
        self.model = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster):
        self.model = model
        self.cluster = kube_cluster

        for pod_fullname, containers in self.cluster.containers:
            compute_node = Compute(pod_fullname)
            for container in containers:
                service_nodes = [s for s in model.services
                                 if check_kobject_node_name_match(container, s, defining_obj_fullname=pod_fullname)]

                if len(service_nodes) > 0:
                    self._add_compute_node_if_not_present(compute_node)
                    model.add_deployed_on(source_node=service_nodes[0], target_node=compute_node)

    def _add_compute_node_if_not_present(self, compute_node: Compute):
        if compute_node not in self.model.computes:
            self.model.add_node(compute_node)


