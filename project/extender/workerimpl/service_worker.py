from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Compute, Service, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


class ServiceWorker(KubeWorker):
    #TODO manca da mettere il service discovery!

    ''' TODO
    Si potrebbe fare che se trovo già il service nel model, sistemo tutte le relazioni che trovo e le forzo a passare
    dal MessageRouter. Questo però non mi sembra giusto, poiché se il servizio c'è ma non viene utilizzato, significa
    che lo sviluppatore molto probabilmente ne è al corrente.

    Se decido di fare divarsemente, posso fare che cerco tutti i pod esposti dal service e sistemo poi tutte le
    relazioni che mi risultano sbagliate
    '''

    _SVC_HOSTNAME = ".svc.cluster.local"

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        for kube_service_name, exposed_containers in self._build_data_structure(kube_cluster=kube_cluster).items():
            message_router_node = next(iter([mr for mr in model.nodes if mr.name + self._SVC_HOSTNAME == kube_service_name]), None)

            # If node not found
            if message_router_node is None:
                if exposed_containers:
                    message_router_node = MessageRouter(kube_service_name)
                    model.add_node(message_router_node)

                    for container_name in exposed_containers:
                        service_node: Service = next(iter([s for s in model.nodes if s.name == container_name[1]]), None)

                        if service_node is None:
                            pass #TODO se prima faccio il controllo potrebbe non servire far nulla qui

                        # Case: service is edge node without interactions
                        if len(service_node.incoming_interactions) == 0 and service_node in model.edge:
                            kservice: KService = kube_cluster.get_object_by_name_and_kind(message_router_node.name, KObjectKind.SERVICE)
                            if kservice:
                                if kservice.is_reachable_from_outside():
                                    model.edge.add_member(message_router_node)
                                    model.edge.remove_member(service_node)
                                    model.add_interaction(source_node=message_router_node, target_node=service_node)
                                else:
                                    model.add_interaction(source_node=message_router_node, target_node=service_node)
                        else:
                            for r in [r for r in service_node.incoming_interactions if isinstance(r, InteractsWith)]:
                                model.add_interaction(source_node=r.source, target_node=message_router_node)
                                model.delete_relationship(r)
                            model.add_interaction(source_node=message_router_node, target_node=service_node)
            # If node is found but is not MessageRouter
            elif not isinstance(message_router_node, MessageRouter):
                incoming_interactions = message_router_node.incoming_interactions.copy()
                interactions = message_router_node.interactions.copy()

                model.delete_node(message_router_node)
                message_router_node = MessageRouter(kube_service_name)
                model.add_node(message_router_node)

                for r in list(incoming_interactions):
                    model.add_interaction(source_node=r.source, target_node=message_router_node)
                    model.delete_relationship(r)

                for r in list(interactions):
                    model.add_interaction(source_node=message_router_node, target_node=r.target)
                    model.delete_relationship(r)

            # If node is found
            else:
                pass #TODO leggi commento
                ''' 
                Se trovo il nodo del message router ho due strade:
                 A) Me ne frego, perché comunque assumo che sia tutto giusto così come sia (niente è stato dimenticato)  
                 B) Sistemo tutto per passare dal service
                '''

    def _build_data_structure(self, kube_cluster: KCluster) -> (str, str):
        result = {}

        for service in kube_cluster.get_objects_by_kind(KObjectKind.SERVICE):
            name = service.get_name_dot_namespace() + self._SVC_HOSTNAME
            if not name in result.keys():
                result[name] = []

            # POD
            for pod_exposed in kube_cluster.find_pods_exposed_by_service(service):
                for container in pod_exposed.get_containers():
                    result[name].append((service.get_name_dot_namespace(), container.name +"."+ pod_exposed.get_name_dot_namespace()))

            # DEPLOYMENT, STATEFULSET, REPLICASET
            for template_defining in kube_cluster.find_pods_defining_object_exposed_by_service(service):
                for container in template_defining.get_containers():
                    result[name].append((service.get_name_dot_namespace(), container.name +"."+ template_defining.get_name_dot_namespace()))

        return result
