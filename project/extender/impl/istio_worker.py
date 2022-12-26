import re
from typing import List

from microfreshener.core.model import MicroToscaModel, MessageRouter, InteractsWith

from project.extender.kubeworker import KubeWorker
from project.extender.impl.service_worker import ServiceWorker
from project.extender.worker_names import ISTIO_WORKER
from project.ignorer.ignore_config import IgnoreConfig
from project.ignorer.ignore_nothing import IgnoreNothing
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_istio import KubeIstioGateway, KubeVirtualService
from project.kmodel.kube_networking import KubeService


def _check_gateway_virtualservice_match(gateway: KubeIstioGateway, virtual_service: KubeVirtualService):
    gateway_check = gateway.fullname in virtual_service.gateways #TODO se è definito solo con name aggiungo .default?

    # New check
    for host in gateway.hosts_exposed:
        # Divide hostname and ns
        if "/" in host:
            namespace, name = host.split("/")[0], host.split("/")[1:]
            if namespace == ".":
                namespace = gateway.namespace
        else:
            namespace, name = "*", host

        # Check namespace
        namespace_check = namespace == "*" or namespace == virtual_service.namespace

        # Check name
        regex = ""
        for c in name:
            regex += "[.]" if c == "." else c if c != "*" else "[a-zA-Z0-9_.]+"

        for svc_host in virtual_service.hosts:
            if re.match(regex, svc_host).string == svc_host:
                return True and namespace_check and gateway_check

        return False


class IstioWorker(KubeWorker):
    GATEWAY_NODE_GENERIC_NAME = "istio-ingress-gateway"

    def __init__(self):
        super().__init__(ISTIO_WORKER)
        self.model = None
        self.cluster: KubeCluster = None
        self.ignore = None
        self.executed_only_after_workers.append(ServiceWorker)

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig):
        self.model = model
        self.cluster = kube_cluster

        if not ignore:
            self.ignore = IgnoreNothing()

        self._search_for_gateways()
        self._search_for_circuit_breaker()
        self._search_for_timeouts()

    def _search_for_timeouts(self):
        self._search_for_timeouts_with_virtual_service()
        self._search_for_timeouts_with_destination_rule()

    def _search_for_timeouts_with_virtual_service(self):
        not_ignored_nodes = self._get_nodes_not_ignored(self.model.message_routers, self.ignore)

        for vservice in self.cluster.virtual_services:
            timeouts: List[(list, str)] = vservice.timeouts
            for (route, destination, timeout) in timeouts:
                if route == destination:
                    node = self.model.get_node_by_name(route, MessageRouter)
                    if node is not None and node in not_ignored_nodes:
                        for interaction in [r for r in node.incoming_interactions if isinstance(r, InteractsWith)]:
                            interaction.set_timeout(True)
                else:
                    route_mr_node = self.model.get_node_by_name(route, MessageRouter)
                    destination_mr_node = self.model.get_node_by_name(destination, MessageRouter)

                    if route_mr_node is not None and destination_mr_node is not None:
                        for r in [r for r in route_mr_node.interactions if r.target == destination_mr_node]:
                            r.set_timeout(True)

    def _search_for_timeouts_with_destination_rule(self):
        not_ignored_nodes = self._get_nodes_not_ignored(self.model.message_routers, self.ignore)

        for rule in self.cluster.destination_rules:
            if rule.timeout is not None:
                mr_node = self.model.get_node_by_name(rule.host, MessageRouter)
                if mr_node in not_ignored_nodes:
                    for r in list(mr_node.incoming_interactions):
                        r.set_timeout(True)

    def _search_for_circuit_breaker(self):
        not_ignored_nodes = self._get_nodes_not_ignored(self.model.nodes, self.ignore)

        for rule in self.cluster.destination_rules:
            if rule.is_circuit_breaker:
                node = self.model.get_node_by_name(rule.host)
                if node is not None and node in not_ignored_nodes:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)

    def _search_for_gateways(self):
        not_ignored_nodes = self._get_nodes_not_ignored(self.model.message_routers, self.ignore)
        gateway_node = self._find_or_create_gateway()

        for gateway in self.cluster.istio_gateways:

            for virtual_service in self.cluster.virtual_services:
                if _check_gateway_virtualservice_match(gateway, virtual_service):

                    for service in self.cluster.services:
                        if service.fullname in virtual_service.destinations:

                            is_one_pod_exposed = self._has_pod_exposed(gateway=gateway, service=service)
                            if is_one_pod_exposed:
                                kube_service_node = self.model.get_node_by_name(service.fullname, MessageRouter)

                                if kube_service_node is not None and kube_service_node in not_ignored_nodes:
                                    self.model.edge.remove_member(kube_service_node)
                                    self.model.add_interaction(source_node=gateway_node, target_node=kube_service_node)

        if len(gateway_node.interactions) + len(gateway_node.incoming_interactions) == 0:
            self.model.delete_node(gateway_node)

    def _find_or_create_gateway(self) -> MessageRouter:
        gateway_node = self.model.get_node_by_name(self.GATEWAY_NODE_GENERIC_NAME, MessageRouter)
        if gateway_node is None:
            gateway_node = MessageRouter(self.GATEWAY_NODE_GENERIC_NAME)
            self.model.edge.add_member(gateway_node)
            self.model.add_node(gateway_node)
        return gateway_node

    def _has_pod_exposed(self, service: KubeService, gateway: KubeIstioGateway):
        for workload in self.cluster.find_workload_exposed_by_svc(service):
            labels = workload.labels
            if len([l for l in labels if l in gateway.selectors]) > 0:
                return True
        return False

