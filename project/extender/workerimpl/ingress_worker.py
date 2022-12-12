from microfreshener.core.model import MicroToscaModel, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.utils import check_kobject_node_name_match


class IngressWorker(KubeWorker):

    INGRESS_CONTROLLER_DEFAULT_NAME = "ingress-controller"

    def __init__(self):
        super().__init__()
        self.model = None
        self.cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster):
        self.model = model
        self.cluster = kube_cluster

        ingress_controller = self._find_or_create_ingress_controller()
        #TODO devo fare un MR per ogni Ingress definito oppure faccio passare tutto dall'Ingress Controller (es. MicroMiner fa così)

        for ingress in self.cluster.ingress:
            for k_service_name in ingress.get_exposed_svc_names():
                k_services = [s for s in self.cluster.services
                              if s.get_fullname() == k_service_name + "." + ingress.namespace]

                if len(k_services) > 0:
                    mr_nodes = [n for n in model.nodes if check_kobject_node_name_match(k_services[0], n)]

                    if len(mr_nodes) > 0:
                        mr_node = mr_nodes[0]
                        kube_service: KubeService = kube_cluster.get_object_by_name(mr_node.name)
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





