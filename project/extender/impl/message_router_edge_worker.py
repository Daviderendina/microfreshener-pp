from microfreshener.core.model import MicroToscaModel

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import MESSAGE_ROUTER_EDGE_WORKER, NAME_WORKER
from project.ignorer.ignore_nothing import IgnoreNothing


class MessageRouterEdgeWorker(KubeWorker):

    def __init__(self):
        super(MessageRouterEdgeWorker, self).__init__(MESSAGE_ROUTER_EDGE_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()) -> MicroToscaModel:
        self._check_services_at_edge(model, cluster, ignorer)
        return model

    def _check_services_at_edge(self, model, cluster, ignorer):
        not_ignored_mr = self._get_nodes_not_ignored(model.message_routers, ignorer)

        for mr_node in [s for s in model.message_routers if s in not_ignored_mr]:
            kube_service = cluster.get_object_by_name(mr_node.name)

            if kube_service.is_reachable_from_outside() and mr_node not in model.edge:
                model.edge.add_member(mr_node)

            elif not kube_service.is_reachable_from_outside() and mr_node in model.edge:
                model.edge.remove_member(mr_node)