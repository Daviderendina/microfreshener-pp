from abc import abstractmethod, ABC

from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Service, Datastore

from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer
from project.kmodel.kPod import KPod


# TODO da rimuovere quando pubblico su pip il package
class Compute(Service):

    def __init__(self, name):
        super(Compute, self).__init__(name)

    def __str__(self):
        return '{} ({})'.format(self.name, 'compute')


# TODO i nomi non mi piacciono
class KubeWorker:

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KCluster) -> MicroToscaModel:
        pass


class IstioWorker(KubeWorker):
    #TODO
        # Aggiorna le relationi nel grafo mettendo service discovery, timeout, circuit breaker
        # what else ?

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        print("Starting Istio worker")


class ContainerWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kubecluster: KCluster):
        print("Starting container worker")  # TODO logger
        for node in list(model.nodes):
            if isinstance(node, Service):
                kobject = kubecluster.get_object_by_name(node.name)

                if kobject is not None and isinstance(kobject, KPod):
                    self._add_compute_nodes(model=model, service_node=node, container_list=kobject.get_containers())
                else:
                    pod_template = kubecluster.get_pod_template_spec_by_name(node.name)
                    if pod_template is not None:
                        self._add_compute_nodes(model=model, service_node=node,
                                                container_list=pod_template.get_containers())
    def _add_compute_nodes(self, model: MicroToscaModel, service_node: Service, container_list: list[KContainer]):
        for container in container_list:
            # TODO qui ho avuto un problema con i nomi. Per ricrearlo, basta usare direttamente container.name al posto di compute_name
            # In pratica, avere un Service e un Compute node con lo stesso nome non è possibile.
            compute_name = container.name + "/" + service_node.name
            compute_node = Compute(compute_name)
            model.add_node(compute_node)
            model.add_interaction(source_node=service_node, target_node=compute_node)


class ServiceWorker(KubeWorker):
    pass
    # TODO controlla che il miner non si sia perso alcun kubernetes Service


class IngressWorker(KubeWorker):
    pass
    # TODO controlla che
    #  i tool non si siano persi alcun Ingress per strada
    #  non si sia perso qualche IngressController (che viene segnato come MsgRouter)


class EdgeWorker(KubeWorker):
    pass
    #TODO effettua una serie di controlli per vedere che non ci siano Proxy, Endpoints, Entrypoint e tutte ste cazzate
    # che espongano i nodi all'esterno


class MessageBrokerWorker(KubeWorker):
    pass
    #TODO non so se serve, controlla che non ci siano MSG broker in giro - non so se i può fare con le info che ho io a disposizione


class DatabaseWorker(KubeWorker):

    DATABASE_PORTS = [1433, 1434, 3306, 3050, 5432, 27017] #TODO cercare tutte le porte standard dei DB

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        for service_node in [s for s in model.nodes if isinstance(s, Service)]:
            kobject = kube_cluster.get_object_by_name(service_node.name)

            if isinstance(kobject, KPod):
                for container in kobject.get_containers():
                    ports = container.get_container_ports()

                    intersection = [v for v in ports if v in self.DATABASE_PORTS]
                    if len(intersection) > 0:

                        # Create datastore node
                        datastore_node = Datastore(service_node.name)

                        # Change incoming_interactions
                        datastore_node.up_interactions = service_node.incoming_interactions

                        # Change interactions
                        #TODO un nodo di tipo Pod non può avere relazioni in uscita. Dovrei chiedere a Jacopo come
                        # funzionano le relazioni perché così non si capisce molto
                        '''
                        for interaction in service_node.interactions:
                            #TODO devo capire bene se funziona lo spostamento delle interactions
                            datastore_node.add_interaction(
                                item=interaction.target,
                                with_timeout=interaction.timeout,
                                with_circuit_breaker=interaction.circuit_breaker,
                                with_dynamic_discovery=interaction.dynamic_discovery
                            )
                        '''

                        # Add nodes to model
                        model.add_node(datastore_node)

