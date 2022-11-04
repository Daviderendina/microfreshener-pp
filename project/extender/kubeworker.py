from abc import abstractmethod, ABC

from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Service, Datastore

from project.kmodel.istio import DestinationRule
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kContainer import KContainer
from project.kmodel.kPod import KPod


# TODO da rimuovere quando pubblico su pip il package
class Compute(Service):

    def __init__(self, name):
        super(Compute, self).__init__(name)

    def __str__(self):
        return '{} ({})'.format(self.name, 'compute')


class KubeWorker:

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
        # Check for gateways - Cerco se sono presenti gateway e li aggiungo? La vedo un po' fine a se stessa come cosa,
        #  in quanto forse non impatterebbe con la ricerca degli smell (vero obiettivo del tool). Questo pensiero può
        #  essere fatto anche per i punti 3 e 4 di _check_for_timeouts TODO Jacopo
        self._check_for_circuit_breaker(model=model, kube_cluster=kube_cluster)
        self._check_for_timeouts(model=model, kube_cluster=kube_cluster)

    def _check_for_timeouts(self, model: MicroToscaModel, kube_cluster: KCluster):
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

    def _check_for_circuit_breaker(self, model: MicroToscaModel, kube_cluster: KCluster):
        # Prendo tutte le DestinationRule
        rules: list[DestinationRule] = kube_cluster.get_objects_by_kind(KObjectKind.ISTIO_DESTINATION_RULE)
        for rule in rules:
            if rule.is_circuit_breaker():
                node = next((n for n in model.nodes if n.name == rule.get_host()), None)
                if node is not None:
                    for r in node.incoming_interactions:
                        r.set_circuit_breaker(True)


class ContainerWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        for node in list(model.nodes):
            if isinstance(node, Service):
                kobject = kube_cluster.get_object_by_full_qualified_name(node.name)

                if kobject is not None and isinstance(kobject, KPod):
                    self._add_compute_nodes(model=model, service_node=node, container_list=kobject.get_containers())
                else:
                    pod_template = kube_cluster.get_pod_template_spec_by_full_qualified_name(node.name)
                    if pod_template is not None:
                        self._add_compute_nodes(model=model, service_node=node,
                                                container_list=pod_template.get_containers())

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


class EdgeWorker(KubeWorker):
    pass
    # TODO effettua una serie di controlli per vedere che non ci siano Proxy, Endpoints, Entrypoint e tutte ste cazzate
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