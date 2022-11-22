from microfreshener.core.model import MicroToscaModel, Service, Datastore

from project.extender.kubeworker import KubeWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer


class DatabaseWorker(KubeWorker):
    DATABASE_PORTS = [1433, 1434, 3306, 3050, 5432, 27017]  # TODO cercare tutte le porte standard dei DB
    DATABASE_NAMES = ["mysql", "mongodb", "mongo-db", "database"]  # TODO ampliare

    def __init__(self):
        super().__init__()
        self.kube_cluster = None
        self.model = None

    def refine(self, model: MicroToscaModel, kube_cluster: KCluster):
        self.model = model
        self.kube_cluster = kube_cluster

        for service_node in [s for s in model.services if len(s.interactions) == 0]:
            container = kube_cluster.get_container_by_tosca_model_name(service_node.name)

            if container is not None and self._is_database(container):
                datastore_node = self._create_datastore_node("TEMPORARY_DATASTORE_NAME")
                self._update_datastore_incoming_interactions(service_node, datastore_node)

                model.delete_node([n for n in model.nodes if n.name == service_node.name][0])
                datastore_node.name = service_node.name

    def _update_datastore_incoming_interactions(self, service_node: Service, datastore_node: Datastore):
        for relation in list(service_node.incoming_interactions):
            self.model.add_interaction(
                source_node=relation.source,
                target_node=datastore_node,
                with_timeout=relation.timeout,
                with_circuit_breaker=relation.circuit_breaker,
                with_dynamic_discovery=relation.dynamic_discovery
            )
            self.model.delete_relationship(relation)

    def _create_datastore_node(self, name: str) -> Datastore:
        datastore_node = Datastore(name)
        self.model.add_node(datastore_node)
        return datastore_node

    def _is_database(self, container: KContainer):
        ports_check = len([v for v in container.get_container_ports() if v in self.DATABASE_PORTS]) > 0
        name_check = len([n for n in self.DATABASE_NAMES if n.upper() in container.name.upper()]) > 0

        return ports_check or name_check
