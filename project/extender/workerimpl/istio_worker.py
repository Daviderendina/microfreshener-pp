from microfreshener.core.model import MicroToscaModel, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.istio import Gateway, VirtualService, DestinationRule
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


def _check_gateway_virtualservice_match(gateway: Gateway, virtual_service: VirtualService):
    gateway_check = gateway.get_name() in virtual_service.get_gateways()  # TODO controllare il formato nomi

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


class IstioWorker(KubeWorker):
    GATEWAY_NODE_GENERIC_NAME = "istio-ingress-gateway"

    # VIRTUAL SERVICE (sentire 4.40 che spiega bene) "from the GATEWAY we will match the HOSTNAME and send traffic to the DESTINATION service"
    #   queste regole vengono applicate quando una richiesta viene mandata all'host

    # GATEWAY devo definire una GATEWAY RESOURCE e (un VIRTUAL SERVICE?). I GATEWAY non hanno routing!!! Espongono e basta porte, protocolli, hostname

    # TODO
    # Aggiorna le relazioni nel grafo mettendo
    # 1) service discovery
    # 2) timeout - c'è da capire se ho coperto tutti i casi possibili
    # 3) circuit breaker - manca la fase di testing
    # 4) Gateway - testare

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        self._search_for_gateways(model=model, kube_cluster=kube_cluster)
        self._search_for_circuit_breaker(model=model, kube_cluster=kube_cluster)
        self._search_for_timeouts(model=model, kube_cluster=kube_cluster)

    def _search_for_timeouts(self, model: MicroToscaModel, kube_cluster: KCluster):
        # Check for timeouts defined with virtual services
        virtual_services = kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_VIRTUAL_SERVICE)
        for vservice in virtual_services:
            timeouts: list[(list, str)] = vservice.get_timeouts()
            for (route, destination, timeout) in timeouts:
                # 1) RUOTE uguale a DESTINATION (a.k.a. HOST)
                if route == destination and kube_cluster.get_container_by_tosca_model_name(destination):
                    # TODO impossibile perché non ho la parte di svc.local.default nel nome che prendo io
                    node = [n for n in model.nodes if n.name == route]
                    if len(node) != 0:
                        for interaction in list(node.incoming_interactions):
                            interaction.set_timeout(True)
                            '''
                            In questo caso, ho fatto che il timeout viene direttamente applicato a tutte le connessioni 
                            in entrata al pod. Forse però questo è sbagliato, o forse sarebbe meglio
                            mettere davanti al pod un MessageRouter (il VirtualService) che comunica attraverso 
                            timeout con il pod.
                            '''  # TODO chiedere a Jacopo

                # 2) RUOTE è un URL/la wildcard *
                # Anche di questi due casi probabilmente posso fottermene TODO Jacopo

                # 4) ROUTE e DESTINATION sono due servizi diversi  -> trovo quella relazione e la cambio, ma è un caso
                # Chiedere a Jacopo, ma per me questo caso semplicemente non esiste.

        # Check for timeouts defined with destination rule
        # Devo capire il campo ConnectionPoolSettings.TCPSettings.connectionTimeout come funziona #TODO

    def _search_for_circuit_breaker(self, model: MicroToscaModel, kube_cluster: KCluster):
        # Prendo tutte le DestinationRule
        rules: list[DestinationRule] = kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE)
        for rule in rules:
            if rule.is_circuit_breaker():
                node = next(iter([n for n in model.nodes if n.name == rule.get_host()]),
                            None)  # TODO occhio qui ai nomi
                if node is not None:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)

    def _search_for_gateways(self, model, kube_cluster):
        gateway_node = next(iter([n for n in model.nodes if n.name == self.GATEWAY_NODE_GENERIC_NAME]), None)
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

                            is_one_pod_exposed = _check_is_one_pod_exposed()

                            if is_one_pod_exposed:
                                service_node = next(iter([n for n in model.nodes if n.name == service.get_name_dot_namespace() + ".svc.local.cluster"]), None)

                                if service_node is not None:
                                    model.edge.remove_member(service_node)
                                    model.add_interaction(source_node=gateway_node, target_node=service_node)
