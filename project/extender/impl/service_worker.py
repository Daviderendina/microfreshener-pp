
from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Service, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import SERVICE_WORKER, NAME_WORKER
from project.ignorer.impl.ignore_nothing import IgnoreNothing


class ServiceWorker(KubeWorker):

    def __init__(self):
        super().__init__(SERVICE_WORKER)
        self.executed_only_after_workers.append(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()) -> MicroToscaModel:
        self._check_message_router_does_not_expose(model, cluster, ignorer)
        return model

    def _check_message_router_does_not_expose(self, model, cluster, ignorer):
        not_ignored_nodes = self._get_nodes_not_ignored(model.nodes, ignorer)

        for k_service in cluster.services:
            mr_node = model.get_node_by_name(k_service.typed_fullname, MessageRouter)

            if mr_node:
                if mr_node in not_ignored_nodes:
                    self._handle_mr_node_found(model, mr_node)
            else:
                generic_node = model.get_node_by_name(k_service.typed_fullname)
                if generic_node is None:
                    self._handle_mr_node_not_found(model, cluster, k_service)
                else:
                    self._handle_found_not_message_router(model, k_service, generic_node)

    def _handle_mr_node_found(self, model, mr_node: MessageRouter):
        for service_node in [i.target for i in mr_node.interactions if isinstance(i.target, Service)]:
            for interaction in [i for i in service_node.incoming_interactions if isinstance(i.source, Service)]:
                model.add_interaction(source_node=interaction.source, target_node=mr_node)
                model.delete_relationship(interaction)

    def _handle_mr_node_not_found(self, model, cluster, k_service):
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

                    to_relink = [r for r in service_node.incoming_interactions if isinstance(r, InteractsWith)]
                    self._relink_relations(model, new_target=mr_node, relations=to_relink)

                    model.add_interaction(source_node=mr_node, target_node=service_node)

        if len(mr_node.incoming_interactions) + len(mr_node.interactions) == 0:
            model.delete_node(mr_node)

    def _handle_found_not_message_router(self, model, k_service, message_router_node):
        incoming_interactions = message_router_node.incoming_interactions.copy()
        interactions = message_router_node.interactions.copy()

        model.delete_node(message_router_node)
        message_router_node = MessageRouter(k_service.typed_fullname)
        model.add_node(message_router_node)

        self._relink_relations(model, new_target=message_router_node, relations=list(incoming_interactions))
        self._relink_relations(model, new_source=message_router_node, relations=list(interactions))

        #TODO eventualmente qui posso chiamare handle_mr_node_not_found

    def _relink_relations(self, model, relations: list, new_source=None, new_target=None):
        for r in relations:
            model.add_interaction(
                source_node=new_source if new_source else r.source,
                target_node=new_target if new_target else r.target)
            model.delete_relationship(r)


