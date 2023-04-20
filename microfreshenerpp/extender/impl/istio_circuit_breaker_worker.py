from microfreshenerpp.extender.kubeworker import KubeWorker
from microfreshenerpp.extender.worker_names import ISTIO_CIRCUIT_BREAKER, NAME_WORKER
from microfreshenerpp.ignorer.impl.ignore_nothing import IgnoreNothing
from microfreshenerpp.kmodel.shortnames import ALL_SHORTNAMES, KUBE_SERVICE
from microfreshenerpp.kmodel.utils import name_is_FQDN


class IstioCircuitBreakerWorker(KubeWorker):

    def __init__(self):
        super(IstioCircuitBreakerWorker, self).__init__(ISTIO_CIRCUIT_BREAKER)
        self.executed_only_after_workers.append(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._search_for_circuit_breaker(model, cluster, ignorer)
        return model

    def _search_for_circuit_breaker(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.nodes, ignorer)

        for rule in cluster.destination_rules:
            if rule.is_circuit_breaker:
                host = self._adjust_host_name(rule.host)
                node = model.get_node_by_name(host)

                if node is not None and node in not_ignored_nodes:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)

    def _adjust_host_name(self, name):
        if name_is_FQDN(name):  # Name is name.namespace.shortname.cluster.local
            return ".".join(name.split(".")[:-2])

        if name.split(".")[-1] in ALL_SHORTNAMES:  # Name is name.namespace.shortname
            return name
        else:
            return f"{name}.{KUBE_SERVICE}"  # Name is name.namespace
