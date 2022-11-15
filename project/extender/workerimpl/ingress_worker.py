from microfreshener.core.model import MicroToscaModel, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


class IngressWorker(KubeWorker):

    INGRESS_CONTROLLER_DEFAULT_NAME = "ingress-controller"

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        ingress_controller = None

        for mr in [n for n in model.nodes if isinstance(n, MessageRouter)]:
            if "ingress" in mr.name and "controller" in mr.name and mr in model.edge:
                ingress_controller = mr
        if not ingress_controller:
            ingress_controller = MessageRouter(self.INGRESS_CONTROLLER_DEFAULT_NAME)
            model.add_node(ingress_controller) #TODO se non ha relazioni alla fine lo tolgo
            model.edge.add_member(ingress_controller)

        # Prendo tutti gli Ingress definiti
        for ingress in kube_cluster.get_objects_by_kind(KObjectKind.INGRESS):
            for service in ingress.get_exposed_svc_names():
                node_name = service + "." + ingress.get_namespace() + ".svc.cluster.local"
                mr_node = next(iter([n for n in model.nodes if n.name == node_name]), None)
                if mr_node:
                    kube_service: KService = kube_cluster.get_object_by_name_and_kind(node_name, KObjectKind.SERVICE)
                    if kube_service:
                        if not kube_service.is_reachable_from_outside():
                            model.edge.remove_member(mr_node)

                    model.add_interaction(source_node=ingress_controller, target_node=mr_node)



