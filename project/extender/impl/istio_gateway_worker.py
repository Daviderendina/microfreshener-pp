import re

from microfreshener.core.model import MessageRouter

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import ISTIO_GATEWAY_WORKER, NAME_WORKER, SERVICE_WORKER
from project.ignorer.impl.ignore_nothing import IgnoreNothing
from project.kmodel.kube_istio import KubeIstioGateway, KubeVirtualService
from project.kmodel.kube_networking import KubeService
from project.kmodel.utils import does_selectors_labels_match


class IstioGatewayWorker(KubeWorker):

    GATEWAY_NODE_GENERIC_NAME = "istio-ingress-gateway"

    def __init__(self):
        super().__init__(ISTIO_GATEWAY_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)
        self.executed_only_after_workers.append(SERVICE_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._search_for_gateways(model, cluster, ignorer)
        return model

    def _search_for_gateways(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.message_routers, ignorer)
        gateway_node = self._find_or_create_gateway(model)

        for gateway in cluster.istio_gateways:

            for virtual_service in cluster.virtual_services:
                if self._check_gateway_virtualservice_match(gateway, virtual_service):

                    for service in cluster.services:
                        if service.fullname in virtual_service.destinations \
                                or service.typed_fullname in virtual_service.destinations:

                            is_one_pod_exposed = self._has_pod_exposed(service, gateway, cluster)
                            if is_one_pod_exposed:
                                kube_service_node = model.get_node_by_name(service.fullname, MessageRouter)

                                if kube_service_node is not None and kube_service_node in not_ignored_nodes:
                                    model.edge.remove_member(kube_service_node)
                                    model.add_interaction(source_node=gateway_node, target_node=kube_service_node)

        if len(gateway_node.interactions) + len(gateway_node.incoming_interactions) == 0:
            model.delete_node(gateway_node)

    def _find_or_create_gateway(self, model) -> MessageRouter:
        gateway_node = model.get_node_by_name(self.GATEWAY_NODE_GENERIC_NAME, MessageRouter)

        if gateway_node is None:
            gateway_node = MessageRouter(self.GATEWAY_NODE_GENERIC_NAME)

            model.edge.add_member(gateway_node)
            model.add_node(gateway_node)

        return gateway_node

    def _has_pod_exposed(self, service: KubeService, gateway: KubeIstioGateway, cluster):
        for workload in cluster.find_workload_exposed_by_svc(service):
            if does_selectors_labels_match(gateway.selectors, workload.labels):
                return True
        return False

    def _check_gateway_virtualservice_match(self, gateway: KubeIstioGateway, virtual_service: KubeVirtualService):
        gateway_check = gateway.fullname in virtual_service.gateways

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
