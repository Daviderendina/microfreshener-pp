from microfreshener.core.model import MicroToscaModel, Service, Datastore

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import DATABASE_WORKER
from project.ignorer.ignore_config import IgnoreConfig
from project.ignorer.ignore_nothing import IgnoreNothing
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer


class DatabaseWorker(KubeWorker):
    DATABASE_PORTS = [1433, 1434, 1521, 3306, 33060, 3050, 5432, 8001, 8080, 27017, 7199, 8089, 443, 10000,
                      8086, 7474, 7473]
    DATABASE_NAMES = ["mysql", "sql", "oracle", "redis", "mongodb", "mongo-db", "database", "mariadb"
                      "snowflake", "cassandra", "splunk", "dynamodb", "hive", "influxdb", "neo4j"]

    def __init__(self):
        super().__init__(DATABASE_WORKER)
        self.cluster = None
        self.model = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig):
        self.model = model
        self.cluster = kube_cluster

        if not ignore:
            ignore = IgnoreNothing()
        not_ignored_services = self._get_nodes_not_ignored(self.model.services, ignore)

        for service_node in [s for s in not_ignored_services if len(s.interactions) == 0]:
            container = kube_cluster.get_object_by_name(service_node.name)

            if container and isinstance(container, KubeContainer) and self._is_database(container):
                datastore_node = self._create_datastore_node("TEMPORARY_DATASTORE_NAME")
                self._update_datastore_incoming_interactions(service_node, datastore_node)

                model.delete_node([n for n in model.nodes if n.name == service_node.name][0])
                datastore_node.name = service_node.name
                #TODO rivedere qui

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

    def _is_database(self, container: KubeContainer):
        ports_check = len([v for v in container.get_container_ports_numbers() if v in self.DATABASE_PORTS]) > 0
        name_check = len([n for n in self.DATABASE_NAMES if n.upper() in container.name.upper()]) > 0

        return ports_check or name_check