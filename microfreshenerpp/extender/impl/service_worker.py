
from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Service, MessageRouter

from microfreshenerpp.extender.kubeworker import KubeWorker
from microfreshenerpp.extender.worker_names import SERVICE_WORKER, NAME_WORKER
from microfreshenerpp.ignorer.impl.ignore_nothing import IgnoreNothing
from microfreshenerpp.kmodel.kube_networking import KubeService


class ServiceWorker(KubeWorker):

    def __init__(self):
        super().__init__(SERVICE_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()) -> MicroToscaModel:
        self._add_not_present_kservices(model, cluster)
        self._check_message_router_does_not_expose(model, cluster, ignorer)
        return model

    def _add_not_present_kservices(self, model, cluster):
        for k_service in cluster.services:
            if model.get_node_by_name(k_service.typed_fullname) is None:

                mr_node = MessageRouter(k_service.typed_fullname)
                model.add_node(mr_node)

                for workload in cluster.find_workload_exposed_by_svc(k_service):
                    for container in workload.containers:

                        service_node = model.get_node_by_name(container.typed_fullname)
                        if service_node is not None:

                            # Fix edge group
                            if k_service.is_reachable_from_outside() and service_node in model.edge:
                                model.edge.add_member(mr_node)
                                model.edge.remove_member(service_node)

                            # Relink direct Service interactions
                            to_relink = [r for r in service_node.incoming_interactions
                                         if isinstance(r, InteractsWith) and isinstance(r.source, Service)]
                            for r in to_relink:
                                r.source.add_interaction(mr_node)
                                model.delete_relationship(r)

                            model.add_interaction(source_node=mr_node, target_node=service_node)

                if len(mr_node.incoming_interactions) + len(mr_node.interactions) == 0:
                    model.delete_node(mr_node)

    def _check_message_router_does_not_expose(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.nodes, ignorer)

        for k_service in cluster.services:
            mr_node = model.get_node_by_name(k_service.typed_fullname)

            if mr_node and mr_node in not_ignored_nodes:
                if not isinstance(mr_node, MessageRouter):
                    mr_node = self._convert_node_to_message_router(model, mr_node)

                self._check_for_missing_interactions(model, cluster, mr_node, k_service)

    def _convert_node_to_message_router(self, model, node):
        incoming_interactions = node.incoming_interactions.copy()
        interactions = node.interactions.copy()

        model.delete_node(node)
        message_router_node = MessageRouter(node.name)
        model.add_node(message_router_node)

        for r in incoming_interactions:
            r.source.add_interaction(message_router_node)
            model.delete_relationship(r)

        for r in interactions:
            message_router_node.add_interaction(r.target)
            model.delete_relationship(r)

        return message_router_node

    def _check_for_missing_interactions(self, model, cluster, mr_node: MessageRouter, k_service: KubeService):
        for workload in cluster.workloads:
            if k_service.does_expose_workload(workload):

                for container in workload.containers:
                    container_exposed = k_service.does_match_ports(container.ports)
                    service_node = model.get_node_by_name(container.typed_fullname, Service)

                    if service_node and container_exposed:
                        if service_node not in [n.target for n in mr_node.interactions].copy():
                            model.add_interaction(mr_node, service_node)

                        for incoming_link in [l for l in service_node.incoming_interactions if isinstance(l.source, Service)]:
                            model.add_interaction(incoming_link.source, mr_node)
                            model.delete_relationship(incoming_link)


