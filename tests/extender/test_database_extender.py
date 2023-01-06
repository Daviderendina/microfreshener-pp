import copy
from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Datastore

from project.extender.extender import KubeExtender
from project.extender.extender import DatabaseWorker
from project.extender.worker_names import DATABASE_WORKER

from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.kmodel.kube_workload import KubePod


class TestDatabaseExtender(TestCase):

    def test_database_found_with_port(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))

        # Change pod port
        container_to_change: KubeContainer = pod.containers[0]
        for port in container_to_change.ports:
            port["containerPort"] = 3306

        cluster.add_object(pod)

        database_node = Service(pod.containers[0].name + "." + pod.typed_fullname)
        model.add_node(database_node)
        svc_uses_db1 = Service("svcUses1")
        svc_uses_db2 = Service("svcUses2")
        model.add_node(svc_uses_db1)
        model.add_node(svc_uses_db2)
        model.add_interaction(source_node=svc_uses_db1, target_node=database_node)
        model.add_interaction(source_node=svc_uses_db2, target_node=database_node)

        extender: KubeExtender = KubeExtender([DATABASE_WORKER])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        database_node = [n for n in model.nodes if n.name == database_node.name][0]

        # Check that Service node had been converted to Database
        self.assertTrue(isinstance(database_node, Datastore))

        # Check that interactions had been maintained
        self.assertEqual(len(svc_uses_db1.incoming_interactions), 0)
        self.assertEqual(len(svc_uses_db1.interactions), 1)
        self.assertEqual(len(svc_uses_db2.incoming_interactions), 0)
        self.assertEqual(len(svc_uses_db2.interactions), 1)
        self.assertEqual(len(database_node.incoming_interactions), 2)
        self.assertEqual(len(database_node.interactions), 0)

    def test_database_found_with_name(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))

        # Change pod port
        container_to_change: KubeContainer = pod.containers[0]
        container_to_change.data["name"] = "mysql-database"
        for port in container_to_change.ports:
            port["containerPort"] = 0

        cluster.add_object(pod)

        database_node = Service(pod.containers[0].name + "." + pod.typed_fullname)
        svc_uses_db1 = Service("svcUses1")
        svc_uses_db2 = Service("svcUses2")
        model.add_node(database_node)
        model.add_node(svc_uses_db1)
        model.add_node(svc_uses_db2)
        model.add_interaction(source_node=svc_uses_db1, target_node=database_node)
        model.add_interaction(source_node=svc_uses_db2, target_node=database_node)

        extender: KubeExtender = KubeExtender([DATABASE_WORKER])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        database_node = [n for n in model.nodes if n.name == database_node.name][0]

        # Check that Service node had been converted to Database
        self.assertTrue(isinstance(database_node, Datastore))

        # Check that interactions had been maintained
        self.assertEqual(len(svc_uses_db1.incoming_interactions), 0)
        self.assertEqual(len(svc_uses_db1.interactions), 1)
        self.assertEqual(len(svc_uses_db2.incoming_interactions), 0)
        self.assertEqual(len(svc_uses_db2.interactions), 1)
        self.assertEqual(len(database_node.incoming_interactions), 2)
        self.assertEqual(len(database_node.interactions), 0)

    def test_database_not_found(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))

        # Change pod port
        container_to_change: KubeContainer = pod.containers[0]
        container_to_change.data["name"] = "container"
        for port in container_to_change.ports:
            port["containerPort"] = 80

        cluster.add_object(pod)

        model.add_node(Service(pod.containers[0].name + "." + pod.typed_fullname))

        extender: KubeExtender = KubeExtender([DATABASE_WORKER])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        # Check that Service node had not been converted to Database
        self.assertFalse(isinstance(list(model.nodes)[0], Datastore))
