from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel, InteractsWith
from microfreshener.core.model.nodes import Service, Datastore, MessageRouter, Compute

from project.kmodel.istio import DestinationRule, Gateway, VirtualService
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kContainer import KContainer


class KubeWorker:
    # TODO devono avere un ordine di exec perché ad esempio quello dei service va fatto prima di quello di istio

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass



class ContainerWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        pods = [(p.get_name_dot_namespace(), p.get_containers()) for p in kube_cluster.get_objects_by_kind(KObjectKind.POD)]
        pods += [(p.get_name_dot_namespace(), p.get_pod_template_spec().get_containers()) for p in
                 kube_cluster.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.REPLICASET, KObjectKind.STATEFULSET)]

        for pod_name_dot_namespace, containers in pods:
            compute_node = Compute(pod_name_dot_namespace)
            added = False
            for container in containers:
                container_fullname = container.name + "." + pod_name_dot_namespace
                service_node = next(iter([s for s in model.nodes if s.name == container_fullname]), None)
                # TODO se non trova il nodo nel modello TOSCA, non lo aggiunge
                if service_node is not None:
                    if not added:
                        model.add_node(compute_node)
                        added = True

                    model.add_deployed_on(source_node=service_node, target_node=compute_node)

    def _add_compute_nodes(self, model: MicroToscaModel, service_node: Service, container_list: list[KContainer]):
        for container in container_list:
            compute_name = container.name + "/" + service_node.name
            compute_node = Compute(compute_name)
            model.add_node(compute_node)
            model.add_interaction(source_node=service_node, target_node=compute_node)


class IngressWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        pass
    # TODO controlla che
    #  i tool non si siano persi alcun Ingress per strada
    #  non si sia perso qualche IngressController (che viene segnato come MsgRouter)
    #  potrebbe anche sistemare il fatto delle relazioni
    # Sembra che il miner si preoccupi solo del controller, probabilmente perché le route le prende dinamicamente

    # Prima di aggiungere la risorsa, devo accertarmi che ci sia almeno un controller disponibile per gestirla, altrimenti ignoro tutto


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


class EdgeWorker(KubeWorker):
    pass
    # TODO effettua una serie di controlli per vedere che non ci siano Proxy, Endpoints, Entrypoint (?) e tutte ste cazzate
    # che espongano i nodi all'esterno ---> Non penso sia necessario


class MessageBrokerWorker(KubeWorker):
    pass
    # TODO non so se serve, controlla che non ci siano MSG broker in giro - non so se i può fare con le info che ho io a disposizione


class DatabaseWorker(KubeWorker):
    DATABASE_PORTS = [1433, 1434, 3306, 3050, 5432, 27017]  # TODO cercare tutte le porte standard dei DB

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        for service_node in [s for s in model.nodes if isinstance(s, Service)]:
            container = kube_cluster.get_container_by_tosca_model_name(service_node.name)

            if container is not None:
                is_database = len([v for v in container.get_container_ports() if v in self.DATABASE_PORTS]) > 0

                if is_database:
                    tmp_name = "TEMPORARY_DATASTORE_NAME"

                    # Create datastore node
                    datastore_node = Datastore(tmp_name)
                    model.add_node(datastore_node)

                    # Change incoming_interactions
                    for relation in list(service_node.incoming_interactions):
                        model.add_interaction(
                            source_node=relation.source,
                            target_node=datastore_node,
                            with_timeout=relation.timeout,
                            with_circuit_breaker=relation.circuit_breaker,
                            with_dynamic_discovery=relation.dynamic_discovery
                        )
                        model.delete_relationship(relation)

                    model.delete_node([n for n in model.nodes if n.name == service_node.name][0])
                    datastore_node.name = service_node.name

                    # Change interactions
                    # TODO un nodo di tipo Datastore non può avere relazioni in uscita. Dovrei chiedere a Jacopo come
                    # funzionano le relazioni perché così non si capisce molto, ma potrei semplicemente non preoccuparmene
                    # Alternativa potrebbe essere evitare di mettere il datastore se ci sono relazioni in uscita
