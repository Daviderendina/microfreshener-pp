from microfreshener.core.model import MessageRouter, InteractsWith

from microfreshenerpp.extender.kubeworker import KubeWorker
from microfreshenerpp.extender.worker_names import ISTIO_TIMEOUT_WORKER, NAME_WORKER
from microfreshenerpp.ignorer.impl.ignore_nothing import IgnoreNothing


class IstioTimeoutWorker(KubeWorker):

    def __init__(self):
        super().__init__(ISTIO_TIMEOUT_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._search_for_timeouts_with_virtual_service(model, cluster, ignorer)
        self._search_for_timeouts_with_destination_rule(model, cluster, ignorer)
        return model

    def _search_for_timeouts_with_virtual_service(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.message_routers, ignorer)

        for vservice in cluster.virtual_services:
            for (route, destination, timeout) in vservice.timeouts:

                if route == destination:
                    node = model.get_node_by_name(route, MessageRouter)

                    if node is not None and node in not_ignored_nodes:
                        for interaction in [r for r in node.incoming_interactions if isinstance(r, InteractsWith)]:
                            interaction.set_timeout(True)

                else:
                    route_mr_node = model.get_node_by_name(route, MessageRouter)
                    destination_mr_node = model.get_node_by_name(destination, MessageRouter)

                    if route_mr_node is not None and destination_mr_node is not None:
                        for r in [r for r in route_mr_node.interactions if r.target == destination_mr_node]:
                            r.set_timeout(True)

    def _search_for_timeouts_with_destination_rule(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.message_routers, ignorer)

        for rule in cluster.destination_rules:
            if rule.timeout is not None:
                mr_node = model.get_node_by_name(rule.host, MessageRouter)

                if mr_node in not_ignored_nodes:
                    for r in list(mr_node.incoming_interactions):
                        r.set_timeout(True)
