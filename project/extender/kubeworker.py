from abc import abstractmethod, ABC

from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Service, Datastore, MessageRouter, Compute

from project.kmodel.istio import DestinationRule
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kContainer import KContainer
from project.kmodel.kPod import KPod

from project.kmodel.kService import KService


class KubeWorker:
    # TODO devono avere un ordine di exec perché ad esempio quello dei service va fatto prima di quello di istio

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass


class IstioWorker(KubeWorker):
    # TODO
    # Aggiorna le relazioni nel grafo mettendo
    # 1) service discovery
    # 2) timeout - c'è da capire se ho coperto tutti i casi possibili
    # 3) circuit breaker - manca la fase di testing

    # Inoltre c'è da vedere se aggiungere anche i Gateway

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
                if route == destination and kube_cluster.get_object_by_full_qualified_name(destination):
                    # TODO impossibile perché non ho la parte di svc.local.default nel nome che prendo io
                    node = [n for n in model.nodes if n.name == route]
                    if len(node) != 0:
                        for interaction in list(node.incoming_interactions):
                            interaction.set_timeout(True)
                            '''
                                In questo caso, ho fatto che il timeout viene direttamente applicato a tutte le 
                                connessioni in entrata al pod. Forse però questo è sbagliato, o forse sarebbe meglio
                                mettere davanti al pod un MessageRouter (il VirtualService) che comunica attraverso 
                                timeout con il pod.
                                '''  # TODO chiedere a Jacopo

                # 2) RUOTE è un URL
                # 3) ROUTE è la wildcard *
                # Anche di questi due casi probabilmente posso fottermene TODO Jacopo

                # 4) ROUTE e DESTINATION sono due servizi diversi  -> trovo quella relazione e la cambio, ma è un caso
                # Chiedere a Jacopo, ma per me questo caso semplicemente non esiste. TODO Jacopo

        # Check for timeouts defined with destination rule
        # Devo capire il campo ConnectionPoolSettings.TCPSettings.connectionTimeout come funziona #TODO

    def _search_for_circuit_breaker(self, model: MicroToscaModel, kube_cluster: KCluster):
        # Prendo tutte le DestinationRule
        rules: list[DestinationRule] = kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE)
        for rule in rules:
            if rule.is_circuit_breaker():
                node = next((n for n in model.nodes if n.name == rule.get_host()), None)
                if node is not None:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)

    def _search_for_gateways(self, model, kube_cluster):
        # TODO per prima cosa c'è da capire come funziona il campo selector e che relazione abbia con i pod.
        virtual_services = kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_VIRTUAL_SERVICE)

        for gateway in kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_GATEWAY):
            gateway_vs = [vs for vs in virtual_services
                          if gateway.spec.name in vs.get_gateways() and vs.get_namespace() == gateway.get_namespace()]
            #TODO namespace

            if len(gateway_vs) > 0:
                gateway_node = MessageRouter(gateway.get_name_dot_namespace())
                model.edge.add_member(gateway_node)
                model.add_node(gateway_node)

                # TODO ma il nodo VirtualService va aggiunto come MessageRouter?
                for vs in gateway_vs:
                    destinations = vs.get_destinations_with_namespace()
                    tosca_service_nodes = [s for s in model.nodes if isinstance(s, Service) and s.name in destinations]

                    for node in tosca_service_nodes:
                        model.add_interaction(source_node=gateway_node, target_node=node) # TODO service discovery ?
                        model.edge.remove_member(node)
            else:
                pass #TODO cosa faccio?


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
    ''' TODO
    Si potrebbe fare che se trovo già il service nel model, sistemo tutte le relazioni che trovo e le forzo a passare
    dal MessageRouter. Questo però non mi sembra giusto, poiché se il servizio c'è ma non viene utilizzato, significa
    che lo sviluppatore molto probabilmente ne è al corrente.

    Se decido di fare divarsemente, posso fare che cerco tutti i pod esposti dal service e sistemo poi tutte le
    relazioni che mi risultano sbagliate
    '''

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        for svc in kube_cluster.get_objects_by_kind(KObjectKind.SERVICE):
            if not self._is_svc_in_model(model=model, service=svc):
                node_name = svc.get_name_dot_namespace() + ".svc.cluster.local"
                message_router_node = MessageRouter(name=node_name)
                if self._is_edge_service(message_router_node):
                    model.edge.add_member(message_router_node)
                model.add_node(message_router_node)

                # TODO prima bisogna capire se un Service rappresenta un Pod oppure un Container
                exponed_pods = kube_cluster.find_pods_exposed_by_service(service=svc)

                for pod in exponed_pods:
                    service_found: Service = self._find_tosca_service_by_pod(model=model, pod=pod)
                    model.add_interaction(source_node=message_router_node,
                                          target_node=service_found)  # TODO non sono sicuro questo funzioni
                    for relationship in service_found.incoming_interactions:
                        relationship.target_node = message_router_node
                        relationship.service_discovery = True

    def _is_svc_in_model(self, model: MicroToscaModel, service: KService):
        search_name = service.get_name_dot_namespace()
        return search_name in list(map(lambda node: node.name, model.nodes))

    def _find_tosca_service_by_pod(self, model: MicroToscaModel, pod: KPod) -> Service:
        for node in model.nodes:
            if node.name == pod.get_name_dot_namespace():  # TODO occhio al nome
                return node

    def _is_edge_service(self, service: KService):
        # TODO è tutto?
        return service.spec.type == "NodePort" or service.spec.type == "LoadBalancer"  # TODO external name?


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
            kobject = kube_cluster.get_object_by_full_qualified_name(service_node.name)

            if isinstance(kobject, KPod):
                containers = kobject.get_containers()
                if len(containers) == 1:

                    ports = containers[0].get_container_ports()

                    intersection = [v for v in ports if v in self.DATABASE_PORTS]
                    if len(intersection) > 0:
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
