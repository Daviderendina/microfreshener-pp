from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Datastore

from project.extender.extender import KubeExtender
from project.extender.extender import DatabaseWorker
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kContainer import KContainer
from project.kmodel.kPod import KPod

from data.kube_objects_dict import POD_WITH_ONE_CONTAINER


class TestDatabaseExtender(TestCase):

    def test_database_found(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)

        # Change pod port
        container_to_change: KContainer = pod.get_containers()[0]
        for port in container_to_change.ports:
            port["containerPort"] = 3306

        cluster.add_object(pod, KObjectKind.POD)

        databaseNode = Service(pod.get_containers()[0].name + "." + pod.get_name_dot_namespace())
        model.add_node(databaseNode)
        svcUsesDB1 = Service("svcUses1")
        svcUsesDB2 = Service("svcUses2")
        model.add_node(svcUsesDB1)
        model.add_node(svcUsesDB2)
        model.add_interaction(source_node=svcUsesDB1, target_node=databaseNode)
        model.add_interaction(source_node=svcUsesDB2, target_node=databaseNode)

        extender: KubeExtender = KubeExtender(worker_list=[DatabaseWorker()])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        databaseNode = [n for n in model.nodes if n.name == databaseNode.name][0]

        # Check that Service node had been converted to Database
        self.assertTrue(isinstance(databaseNode, Datastore))

        # Check that interactions had been maintained
        self.assertEqual(len(svcUsesDB1.incoming_interactions), 0)
        self.assertEqual(len(svcUsesDB1.interactions), 1)
        self.assertEqual(len(svcUsesDB2.incoming_interactions), 0)
        self.assertEqual(len(svcUsesDB2.interactions), 1)
        self.assertEqual(len(databaseNode.incoming_interactions), 2)
        self.assertEqual(len(databaseNode.interactions), 0)

    def test_database_not_found(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)

        # Change pod port
        container_to_change: KContainer = pod.get_containers()[0]
        for port in container_to_change.ports:
            port["containerPort"] = 80

        cluster.add_object(pod, KObjectKind.POD)

        model.add_node(Service(pod.metadata.name))

        extender: KubeExtender = KubeExtender(worker_list=[DatabaseWorker()])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        # Check that Service node had not been converted to Database
        self.assertFalse(isinstance(list(model.nodes)[0], Datastore))
