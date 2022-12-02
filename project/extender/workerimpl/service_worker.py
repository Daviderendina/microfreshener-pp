from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Service, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kObject import KObject
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind
from project.utils import check_kobject_node_name_match


class ServiceWorker(KubeWorker):
    # TODO ogni volta che inserisco una nuova relazione MR-->SVC oppure aggiungo direttamente un nuovo MR, devo controllare
    # che tutto quello esposto sotto sia compatibile in termini di porte

    def __init__(self):
        super().__init__()
        self.model = None
        self.kube_cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        self.model = model
        self.kube_cluster = kube_cluster

        for k_service, defining_obj in self._get_svc_with_object_exposed():
            mr_node = next(iter([mr for mr in model.nodes if check_kobject_node_name_match(k_service, mr)]), None)

            if mr_node is None:
                self._handle_mr_node_not_found(k_service, defining_obj)
            elif not isinstance(mr_node, MessageRouter):
                self._handle_found_not_message_router(k_service, mr_node)
            else:
                self._handle_mr_node_found(mr_node)

    def _handle_mr_node_found(self, mr_node: MessageRouter):
        # TODO in questo caso non so se è giusto quello che ho fatto, non ho capito bene se:
        # 1) Devo fare così come ho fatto
        # 2) Devo aggiungere un altro nodo che rappresenta quel servizio, tenendo così i due servizi "paralleli"
        for service_node in [i.target for i in mr_node.interactions if isinstance(i, InteractsWith)]:
            for interaction in [i for i in service_node.incoming_interactions if isinstance(i.source, Service)]:
                self.model.add_interaction(source_node=interaction.source, target_node=mr_node)
                self.model.delete_relationship(interaction)

    def _handle_mr_node_not_found(self, k_service: KService, defining_obj: KObject):
        exposed_containers = defining_obj.get_containers()

        if len(exposed_containers) == 0:
            return

        mr_node = MessageRouter(k_service.get_fullname())
        self.model.add_node(mr_node)

        for container in exposed_containers:
            service_node = next(iter([s for s in self.model.services if check_kobject_node_name_match(container, s, defining_obj_fullname=defining_obj.get_fullname())]), None)
            if service_node is not None:

                if k_service.is_reachable_from_outside() and service_node in self.model.edge:
                    self.model.edge.add_member(mr_node)
                    self.model.edge.remove_member(service_node)

                if len(service_node.incoming_interactions) > 0:
                    self._relink_relations(
                        new_target=mr_node,
                        relations=[r for r in service_node.incoming_interactions if isinstance(r, InteractsWith)],
                    )

                self.model.add_interaction(source_node=mr_node, target_node=service_node)

    def _handle_found_not_message_router(self, k_service: KService, message_router_node: MessageRouter):
        incoming_interactions = message_router_node.incoming_interactions.copy()
        interactions = message_router_node.interactions.copy()

        self.model.delete_node(message_router_node)
        message_router_node = MessageRouter(k_service.get_fullname())
        self.model.add_node(message_router_node)

        self._relink_relations(new_target=message_router_node, relations=list(incoming_interactions))
        self._relink_relations(new_source=message_router_node, relations=list(interactions))

    def _relink_relations(self, relations: list, new_source=None, new_target=None):
        for r in relations:
            self.model.add_interaction(
                source_node=new_source if new_source else r.source,
                target_node=new_target if new_target else r.target)
            self.model.delete_relationship(r)

    def _get_svc_with_object_exposed(self) -> list[(KService, KObject)]:
        result = []
        for k_service in self.kube_cluster.get_objects_by_kind(KObjectKind.SERVICE):
            for pod_exposed in self.kube_cluster.find_pods_exposed_by_service(k_service):
                result.append((k_service, pod_exposed))

            for defining_obj in self.kube_cluster.find_defining_obj_exposed_by_service(k_service):
                result.append((k_service, defining_obj))

        return result
