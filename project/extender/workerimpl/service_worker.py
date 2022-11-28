from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Compute, Service, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind

# TODO manca da mettere il service discovery!


class ServiceWorker(KubeWorker):
    #TODO ogni volta che inserisco una nuova relazione MR-->SVC oppure aggiungo direttamente un nuovo MR, devo controllare
    # che tutto quello esposto sotto sia compatibile in termini di porte

    _SVC_HOSTNAME = ".svc.cluster.local"

    def __init__(self):
        super().__init__()
        self.model = None
        self.kube_cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        self.model = model
        self.kube_cluster = kube_cluster
        
        for kube_service_name, exposed_containers in self._build_data_structure(kube_cluster=kube_cluster).items():
            message_router_node = next(iter([mr for mr in model.nodes if mr.name == kube_service_name]), None)

            if message_router_node is None:
                if exposed_containers:
                    self._handle_node_not_found(kube_service_name, exposed_containers)
            elif not isinstance(message_router_node, MessageRouter):
                self._handle_found_not_message_router(kube_service_name, message_router_node)
            else:
                #TODO in questo caso non so se è giusto quello che ho fatto, non ho capito bene se:
                # 1) Devo fare così come ho fatto
                # 2) Devo aggiungere un altro nodo che rappresenta quel servizio, tenendo così i due servizi "paralleli"
                for service_node in [i.target for i in message_router_node.interactions if isinstance(i, InteractsWith)]:
                    for int in [i for i in service_node.incoming_interactions if isinstance(i.source, Service)]:
                        model.add_interaction(source_node=int.source, target_node=message_router_node)
                        model.delete_relationship(int)

    def _handle_node_not_found(self, kube_service_name: str, exposed_containers: list):
        message_router_node = MessageRouter(kube_service_name)
        self.model.add_node(message_router_node)

        for container_name in exposed_containers:
            service_node: Service = next(iter([s for s in self.model.nodes if s.name == container_name[1]]), None)

            if service_node is None:
                # Case: service is edge node without interactions
                if len(service_node.incoming_interactions) == 0 and service_node in self.model.edge:
                    kservice: KService = self.kube_cluster.get_object_by_name(message_router_node.name,
                                                                              KObjectKind.SERVICE)
                    if kservice:
                        if kservice.is_reachable_from_outside():
                            self.model.edge.add_member(message_router_node)
                            self.model.edge.remove_member(service_node)
                        self.model.add_interaction(source_node=message_router_node, target_node=service_node)
                else:
                    self._relink_relations(new_target=message_router_node,
                                           relations=[r for r in service_node.incoming_interactions if
                                                      isinstance(r, InteractsWith)])
                    self.model.add_interaction(source_node=message_router_node, target_node=service_node)

    def _handle_found_not_message_router(self, kube_service_name: str, message_router_node: MessageRouter):
        incoming_interactions = message_router_node.incoming_interactions.copy()
        interactions = message_router_node.interactions.copy()

        self.model.delete_node(message_router_node)
        message_router_node = MessageRouter(kube_service_name)
        self.model.add_node(message_router_node)

        self._relink_relations(new_target=message_router_node, relations=list(incoming_interactions))
        self._relink_relations(new_source=message_router_node, relations=list(interactions))

    def _relink_relations(self, relations: list, new_source=None, new_target=None):
        for r in relations:
            self.model.add_interaction(
                source_node=new_source if new_source else r.source,
                target_node=new_target if new_target else r.target)
            self.model.delete_relationship(r)

    def _build_data_structure(self, kube_cluster: KCluster) -> (str, str):
        result = {}

        for service in kube_cluster.get_objects_by_kind(KObjectKind.SERVICE):
            name = service.get_fullname() + self._SVC_HOSTNAME
            if not name in result.keys():
                result[name] = []

            # POD
            for pod_exposed in kube_cluster.find_pods_exposed_by_service(service):
                for container in pod_exposed.get_containers():
                    result[name].append((service.get_fullname(), container.name + "." + pod_exposed.get_fullname()))

            # DEPLOYMENT, STATEFULSET, REPLICASET
            for template_defining in kube_cluster.find_pods_defining_object_exposed_by_service(service):
                for container in template_defining.get_containers():
                    result[name].append((service.get_fullname(), container.name + "." + template_defining.get_fullname()))

        return result
