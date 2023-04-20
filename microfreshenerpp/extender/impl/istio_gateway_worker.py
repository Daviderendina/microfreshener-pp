import re

from microfreshener.core.model import MessageRouter

from microfreshenerpp.extender.kubeworker import KubeWorker
from microfreshenerpp.extender.worker_names import ISTIO_GATEWAY_WORKER, NAME_WORKER, SERVICE_WORKER
from microfreshenerpp.ignorer.impl.ignore_nothing import IgnoreNothing
from microfreshenerpp.kmodel.kube_istio import KubeIstioGateway, KubeVirtualService
from microfreshenerpp.kmodel.kube_networking import KubeService
from microfreshenerpp.kmodel.utils import does_selectors_labels_match


class IstioGatewayWorker(KubeWorker):

    GATEWAY_NODE_GENERIC_NAME = "istio-ingress-gateway"

    def __init__(self):
        super().__init__(ISTIO_GATEWAY_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)
        self.executed_only_after_workers.append(SERVICE_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()):
        self._search_for_gateways(model, cluster, ignorer)
        return model

    def _create_gateway_node(self, model, gateway):
        gateway_node = MessageRouter(gateway.typed_fullname)
        model.add_node(gateway_node)
        model.edge.add_member(gateway_node)

        return gateway_node


    def _search_for_gateways(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.message_routers, ignorer)

        for gateway in cluster.istio_gateways:
            gateway_node = self._create_gateway_node(model, gateway)

            for virtual_service in cluster.virtual_services:
                if self._check_gateway_virtualservice_match(gateway, virtual_service):

                    for service in cluster.services:
                        if service.fullname in virtual_service.destinations \
                                or service.typed_fullname in virtual_service.destinations:

                            kube_service_node = model.get_node_by_name(service.fullname, MessageRouter)

                            if kube_service_node is not None and kube_service_node in not_ignored_nodes:
                                if kube_service_node in model.edge.members:
                                    model.edge.remove_member(kube_service_node)
                                model.add_interaction(source_node=gateway_node, target_node=kube_service_node)

    def _has_pod_exposed(self, service: KubeService, gateway: KubeIstioGateway, cluster):
        for workload in cluster.find_workload_exposed_by_svc(service):
            if does_selectors_labels_match(gateway.selectors, workload.labels):
                return True
        return False

    def _check_gateway_virtualservice_match(self, gateway: KubeIstioGateway, virtual_service: KubeVirtualService):
        gateway_check = gateway.fullname in virtual_service.gateways

        if gateway_check:
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
