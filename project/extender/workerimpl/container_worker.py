from microfreshener.core.model import MicroToscaModel, Service

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kPod import KPod, KPodSpec
from project.kmodel.kobject_kind import KObjectKind
from project.utils import check_kobject_node_name_match


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
        pod_spec_list: list[(str, KPodSpec)] = self._get_all_pod_spec()

        for defining_obj_fullname, spec in pod_spec_list:
            for container in spec.containers:
                service_nodes = [s for s in self.model.services if
                                 check_kobject_node_name_match(container, s, defining_obj_fullname)]

                if len(service_nodes) > 0:
                    service_node = service_nodes[0]
                    if spec.host_network:
                        self.model.edge.add_member(service_node)
                    else:
                        for port in container.ports:
                            if port.get("host_port", None):
                                self.model.edge.add_member(service_node)

    def _get_all_pod_spec(self) -> list[(str, KPodSpec)]:
        pod_spec_list = []

        for pod in self.kube_cluster.get_objects_by_kind(KObjectKind.POD):
            pod_spec_list.append((pod.get_fullname(), pod.spec))

        list_from_defining_obj = self.kube_cluster.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.STATEFULSET,
                                                                       KObjectKind.REPLICASET)
        for defining_obj in list_from_defining_obj:
            pod_spec_list.append((defining_obj.get_fullname(), defining_obj.spec.template.spec))

        return pod_spec_list
