from microfreshener.core.model import MicroToscaModel, MessageRouter, InteractsWith

from project.extender.kubeworker import KubeWorker
from project.kmodel.istio import Gateway, VirtualService, DestinationRule
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


# TODO per risolvere il problema dei FQDN, si potrebbe fare un mega registro di tutti gli obj definiti in quali namespace.
# Mi sembra però un casino farlo adesso


def _check_gateway_virtualservice_match(gateway: Gateway, virtual_service: VirtualService):
    # TODO a me potrebbe anche non arrivare un FQDN, ma non è semplice risalire alle varie parti del nome (es. non posso estrarre namespace)
    # Ho due strade: (1) Mi interesso solo dei FQDN (e tengo i controllo IN che attualmente è commentato)
    # (2) Faccio il controllo con startsWith, considerando che però potrebbero esserci errori
    # Per ora è attuata la strategia (1)

    gateway_check = gateway.get_name_dot_namespace() in virtual_service.get_gateways()

    gateway_hosts = gateway.get_all_host_exposed()
    virtual_service_hosts = virtual_service.get_hosts()
    host_check = len([h for h in gateway_hosts if h in virtual_service_hosts])

    return host_check and gateway_check


def _check_is_one_pod_exposed(kube_cluster: KCluster, service: KService, gateway: Gateway):
    for pod in kube_cluster.find_pods_exposed_by_service(service):
        pod_labels = pod.get_labels()
        if len([l for l in pod_labels if l in gateway.get_selectors()]):
            return True
    return False


def _find_node_by_name(model: MicroToscaModel, name: str):
    return next(iter([mr for mr in model.nodes if mr.name == name]), None)


class IstioWorker(KubeWorker):
    GATEWAY_NODE_GENERIC_NAME = "istio-ingress-gateway"

    # VIRTUAL SERVICE (sentire 4.40 che spiega bene) "from the GATEWAY we will match the HOSTNAME and send traffic to the DESTINATION service"
    #   queste regole vengono applicate quando una richiesta viene mandata all'host

    # GATEWAY devo definire una GATEWAY RESOURCE e (un VIRTUAL SERVICE?). I GATEWAY non hanno routing!!! Espongono e basta porte, protocolli, hostname

    #TODO mi manca da capire il service discovery

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        self._search_for_gateways(model=model, kube_cluster=kube_cluster)
        self._search_for_circuit_breaker(model=model, kube_cluster=kube_cluster)
        self._search_for_timeouts(model=model, kube_cluster=kube_cluster)

    def _search_for_timeouts(self, model: MicroToscaModel, kube_cluster: KCluster):
        # Check for timeouts defined with VirtualServic
        for vservice in kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_VIRTUAL_SERVICE):
            # TODO anche qui, do per scontato che nei VServices route e destination siamo definiti come FQDN
            timeouts: list[(list, str)] = vservice.get_timeouts()
            for (route, destination, timeout) in timeouts:
                # 1) RUOTE uguale a DESTINATION (a.k.a. HOST)
                if route == destination:
                    node = _find_node_by_name(model, route)
                    if node is not None:
                        for interaction in [r for r in node.incoming_interactions if isinstance(r, InteractsWith)]:
                            interaction.set_timeout(True)

                # 2) RUOTE è un URL/la wildcard *
                # Anche di questi due casi probabilmente posso fottermene TODO Jacopo

                # 4) ROUTE e DESTINATION sono due servizi diversi
                if route != destination:
                    route_mr_node = _find_node_by_name(model, route)
                    destination_mr_node = _find_node_by_name(model, destination)

                    if route_mr_node is not None and destination_mr_node is not None:
                        for r in [r for r in route_mr_node.interactions if r.target == destination_mr_node]:
                            r.set_timeout(True)

        # Check for timeouts defined with DestinationRule
        for rule in kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE):
            if rule.get_timeout() is not None:
                mr_node = _find_node_by_name(rule.get_host())
                for r in list(mr_node.incoming_interactions):
                    r.set_timeout(True)

    def _search_for_circuit_breaker(self, model: MicroToscaModel, kube_cluster: KCluster):
        rules: list[DestinationRule] = kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE)
        for rule in rules:
            if rule.is_circuit_breaker():
                # TODO anche qui suppongo che siano stati usati i FQDN
                node = next(iter([n for n in model.nodes if n.name == rule.get_host()]), None)
                if node is not None:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)

    def _search_for_gateways(self, model, kube_cluster):
        gateway_node = _find_node_by_name(model, self.GATEWAY_NODE_GENERIC_NAME)
        if gateway_node is None:
            gateway_node = MessageRouter(self.GATEWAY_NODE_GENERIC_NAME)
            model.edge.add_member(gateway_node)
            model.add_node(gateway_node)

        for gateway in kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_GATEWAY):

            for virtual_service in kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_VIRTUAL_SERVICE):
                if _check_gateway_virtualservice_match(gateway, virtual_service):

                    # Vado a cercarmi i svc
                    for service in kube_cluster.get_objects_by_kind(KObjectKind.SERVICE):
                        if service.get_name_dot_namespace() in virtual_service.get_destinations():

                            is_one_pod_exposed = _check_is_one_pod_exposed(kube_cluster, gateway, service)
                            if is_one_pod_exposed:
                                service_node = _find_node_by_name(model, service.get_name_dot_namespace()
                                                                       + ".svc.local.cluster")

                                if service_node is not None:
                                    model.edge.remove_member(service_node)
                                    model.add_interaction(source_node=gateway_node, target_node=service_node)
