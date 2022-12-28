from microfreshener.core.model import MessageRouter

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import INGRESS_WORKER
from project.ignorer.ignore_nothing import IgnoreNothing
from project.kmodel.kube_networking import KubeService


class IngressWorker(KubeWorker):

    def __init__(self):
        super().__init__(INGRESS_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        not_ignored_mr = self._get_nodes_not_ignored(model.message_routers, ignorer)

        for ingress in cluster.ingress:
            ingress_node = model.get_node_by_name(ingress.typed_fullname, MessageRouter)

            if ingress_node:
                if ingress_node in not_ignored_mr:
                    self._handle_ingress_in_model(model, cluster, ingress, ingress_node, not_ignored_mr)
            else:
                self._handle_ingress_not_in_model(model, cluster, ingress, ignorer)

    def _handle_ingress_in_model(self, model, cluster, ingress, ingress_node, not_ignored_mr):
        for exposed_svc in ingress.get_exposed_svc_names():
            mr_node = model.get_node_by_name(exposed_svc, MessageRouter)

            if mr_node not in [r.target for r in ingress_node.interactions] and mr_node in not_ignored_mr:
                model.add_interaction(source_node=ingress_node, target_node=mr_node)
                self._remove_mr_from_edge(model, cluster, mr_node)

    def _handle_ingress_not_in_model(self, model, cluster, ingress, ignore):
        not_ignored_nodes = self._get_nodes_not_ignored(list(model.nodes), ignore)

        for k_service_name in ingress.get_exposed_svc_names():
            k_service = cluster.get_object_by_name(k_service_name, KubeService)

            if k_service:
                mr_node = model.get_node_by_name(k_service.typed_fullname)
                if mr_node in not_ignored_nodes:
                    self._remove_mr_from_edge(model, cluster, mr_node)

                    ingress_node = MessageRouter(ingress.typed_fullname)
                    model.add_node(ingress_node)
                    model.edge.add_member(ingress_node)
                    model.add_interaction(source_node=ingress_node, target_node=mr_node)

    def _remove_mr_from_edge(self, model, cluster, node):
        if node in model.edge.members:
            k_service = cluster.get_object_by_name(node.name)
            if k_service and not k_service.is_reachable_from_outside():
                model.edge.remove_member(node)
