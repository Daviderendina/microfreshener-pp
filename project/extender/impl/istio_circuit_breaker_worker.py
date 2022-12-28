from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import ISTIO_CIRCUIT_BREAKER
from project.ignorer.ignore_nothing import IgnoreNothing


class IstioCircuitBreakerWorker(KubeWorker):

    def __init__(self):
        super(IstioCircuitBreakerWorker, self).__init__(ISTIO_CIRCUIT_BREAKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._search_for_circuit_breaker(model, cluster, ignorer)
        return model

    def _search_for_circuit_breaker(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.nodes, ignorer)

        for rule in cluster.destination_rules:
            if rule.is_circuit_breaker:
                node = model.get_node_by_name(rule.host)

                if node is not None and node in not_ignored_nodes:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)
