from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute, Service

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer
from project.kmodel.kobject_kind import KObjectKind


class ContainerWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        pods = [(p.get_name_dot_namespace(), p.get_containers()) for p in kube_cluster.get_objects_by_kind(KObjectKind.POD)]
        pods += [(p.get_name_dot_namespace(), p.get_pod_template_spec().get_containers()) for p in
                 kube_cluster.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.REPLICASET, KObjectKind.STATEFULSET)]

        for pod_name_dot_namespace, containers in pods:
            compute_node = Compute(pod_name_dot_namespace)
            added = False
            for container in containers:
                container_fullname = container.name + "." + pod_name_dot_namespace
                service_node = next(iter([s for s in model.nodes if s.name == container_fullname]), None)
                # TODO se non trova il nodo nel modello TOSCA, non lo aggiunge
                if service_node is not None:
                    if not added:
                        model.add_node(compute_node)
                        added = True

                    model.add_deployed_on(source_node=service_node, target_node=compute_node)

    def _add_compute_nodes(self, model: MicroToscaModel, service_node: Service, container_list: list[KContainer]):
        for container in container_list:
            compute_name = container.name + "/" + service_node.name
            compute_node = Compute(compute_name)
            model.add_node(compute_node)
            model.add_interaction(source_node=service_node, target_node=compute_node)

