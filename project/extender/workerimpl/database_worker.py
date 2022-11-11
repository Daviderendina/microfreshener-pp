from microfreshener.core.model import MicroToscaModel, Service, Datastore

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster


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
