from microfreshener.core.model import MicroToscaModel, MessageRouter, InteractsWith

from project.extender.kubeworker import KubeWorker
from project.kmodel.istio import Gateway, VirtualService, DestinationRule
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


def _check_gateway_virtualservice_match(gateway: Gateway, virtual_service: VirtualService):
    gateway_check = gateway.get_name_dot_namespace() in virtual_service.get_gateways()

    gateway_hosts = gateway.get_all_host_exposed()
    virtual_service_hosts = virtual_service.get_hosts()
    host_check = len([h for h in gateway_hosts if h in virtual_service_hosts])

    return host_check and gateway_check


def _find_node_by_name(model: MicroToscaModel, name: str):
    # TODO forse inventarsi qualcosa di meglio
    return next(iter([mr for mr in model.nodes if mr.name == name]), None)


class IstioWorker(KubeWorker):
    GATEWAY_NODE_GENERIC_NAME = "istio-ingress-gateway"

    # TODO mi manca da capire il service discovery

    def __init__(self):
        self.model = None
        self.kube_cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        self.model = model
        self.kube_cluster = kube_cluster

        self._search_for_gateways()
        self._search_for_circuit_breaker()
        self._search_for_timeouts()

    def _search_for_timeouts(self):
        self._search_for_timeouts_with_virtual_service()
        self._search_for_timeouts_with_destination_rule()

    def _search_for_timeouts_with_virtual_service(self):
        for vservice in self.kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_VIRTUAL_SERVICE):
            # TODO anche qui, do per scontato che nei VServices route e destination siamo definiti come FQDN
            timeouts: list[(list, str)] = vservice.get_timeouts()
            for (route, destination, timeout) in timeouts:
                if route == destination:
                    node = _find_node_by_name(self.model, route)
                    if node is not None:
                        for interaction in [r for r in node.incoming_interactions if isinstance(r, InteractsWith)]:
                            interaction.set_timeout(True)
                else:
                    route_mr_node = _find_node_by_name(self.model, route)
                    destination_mr_node = _find_node_by_name(self.model, destination)

                    if route_mr_node is not None and destination_mr_node is not None:
                        for r in [r for r in route_mr_node.interactions if r.target == destination_mr_node]:
                            r.set_timeout(True)

                # 2) RUOTE è un URL/la wildcard *
                # Anche di questi due casi probabilmente posso fottermene TODO Jacopo

    def _search_for_timeouts_with_destination_rule(self):
        for rule in self.kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE):
            if rule.get_timeout() is not None:
                mr_node = _find_node_by_name(rule.get_host())
                for r in list(mr_node.incoming_interactions):
                    r.set_timeout(True)

    def _search_for_circuit_breaker(self):
        rules: list[DestinationRule] = self.kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE)
        for rule in rules:
            if rule.is_circuit_breaker():
                # TODO anche qui suppongo che siano stati usati i FQDN
                node = next(iter([n for n in self.model.nodes if n.name == rule.get_host()]), None)
                if node is not None:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)

    def _search_for_gateways(self):
        gateway_node = self._find_or_create_gateway()

        for gateway in self.kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_GATEWAY):

            for virtual_service in self.kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_VIRTUAL_SERVICE):
                if _check_gateway_virtualservice_match(gateway, virtual_service):

                    for service in self.kube_cluster.get_objects_by_kind(KObjectKind.SERVICE):
                        if service.get_name_dot_namespace() in virtual_service.get_destinations():

                            is_one_pod_exposed = self._has_pod_exposed(gateway, service)
                            if is_one_pod_exposed:
                                service_node = _find_node_by_name(self.model, service.get_name_dot_namespace()
                                                                  + ".svc.local.cluster")

                                if service_node is not None:
                                    self.model.edge.remove_member(service_node)
                                    self.model.add_interaction(source_node=gateway_node, target_node=service_node)

    def _find_or_create_gateway(self) -> MessageRouter:
        gateway_node = _find_node_by_name(self.model, self.GATEWAY_NODE_GENERIC_NAME)
        if gateway_node is None:
            gateway_node = MessageRouter(self.GATEWAY_NODE_GENERIC_NAME)
            self.model.edge.add_member(gateway_node)
            self.model.add_node(gateway_node)
        return gateway_node

    def _has_pod_exposed(self, service: KService, gateway: Gateway):
        for pod in self.kube_cluster.find_pods_exposed_by_service(service):
            pod_labels = pod.get_labels()
            if len([l for l in pod_labels if l in gateway.get_selectors()]):
                return True
        return False
