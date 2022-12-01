from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kobject_kind import KObjectKind
from project.utils import check_kobject_node_name_match


class ComputeNodeWorker(KubeWorker):

    def __init__(self):
        super().__init__()
        self.kube_cluster = None
        self.model = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        self.model = model
        self.kube_cluster = kube_cluster

        pods = self._get_all_defined_pods()

        for pod_fullname, containers in pods:
            compute_node = Compute(pod_fullname)
            for container in containers:
                service_nodes = [s for s in model.services if check_kobject_node_name_match(container, s, defining_obj_fullname=pod_fullname)]

                if len(service_nodes) > 0:
                    self._add_compute_node_if_not_present(compute_node)
                    model.add_deployed_on(source_node=service_nodes[0], target_node=compute_node)

    def _add_compute_node_if_not_present(self, compute_node: Compute):
        if compute_node not in self.model.computes:
            self.model.add_node(compute_node)

    def _get_all_defined_pods(self):
        pods = [(p.get_fullname(), p.get_containers())
                for p in self.kube_cluster.get_objects_by_kind(KObjectKind.POD)]
        pods += [(p.get_fullname(), p.get_pod_template_spec().get_containers())
                 for p in self.kube_cluster.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.REPLICASET,
                                                  KObjectKind.STATEFULSET)]

        return pods


