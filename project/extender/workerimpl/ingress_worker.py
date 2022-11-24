from microfreshener.core.model import MicroToscaModel, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


class IngressWorker(KubeWorker):

    INGRESS_CONTROLLER_DEFAULT_NAME = "ingress-controller"

    def __init__(self):
        super().__init__()
        self.model = None
        self.kube_cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        self.model = model
        self.kube_cluster = kube_cluster

        ingress_controller = self._find_or_create_ingress_controller()
        #TODO devo fare un MR per ogni Ingress definito oppure faccio passare tutto dall'Ingress Controller (es. MicroMiner fa così)

        for ingress in kube_cluster.get_objects_by_kind(KObjectKind.INGRESS):
            for service in ingress.get_exposed_svc_names():
                node_name = service + "." + ingress.get_namespace() + ".svc.cluster.local"
                mr_node = next(iter([n for n in model.nodes if n.name == node_name]), None)
                if mr_node:
                    kube_service: KService = kube_cluster.get_object_by_name_and_kind(node_name, KObjectKind.SERVICE)
                    if kube_service and not kube_service.is_reachable_from_outside():
                        model.edge.remove_member(mr_node)

                    model.add_interaction(source_node=ingress_controller, target_node=mr_node)

        if len(ingress_controller.interactions) == 0 and len(ingress_controller.incoming_interactions) == 0:
            model.delete_node(ingress_controller)

    def _find_or_create_ingress_controller(self):
        for mr in self.model.message_routers:
            if "ingress" in mr.name and "controller" in mr.name and mr in self.model.edge:
                return mr
        ingress_controller = MessageRouter(self.INGRESS_CONTROLLER_DEFAULT_NAME)
        self.model.add_node(ingress_controller)
        self.model.edge.add_member(ingress_controller)
        return ingress_controller





