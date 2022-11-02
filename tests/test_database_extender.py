from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Datastore

from project.extender.extender import KubeExtender
from project.extender.kubeworker import DatabaseWorker
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kContainer import KContainer
from project.kmodel.kPod import KPod

from tests.kube_objects_dict import POD_WITH_ONE_CONTAINER, POD_WITH_TWO_CONTAINER


class TestDatabaseExtender(TestCase):
    # TODO manca la parte di testing legata alle relazioni tra il nodo che vado a ricreare e gli altri del modello
    # Inoltre non sono molto sicuro che il tutto sia corretto

    def test_database_found(self):

        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)

        # Change pod port
        container_to_change: KContainer = pod.get_containers()[0]
        for port in container_to_change.ports:
            port["containerPort"] = 3306

        cluster.add_object(pod, KObjectKind.POD)

        databaseNode = Service(pod.metadata.name)
        model.add_node(databaseNode)
        svcUsesDB = Service("svcUses")
        svcUsedByDB = Service("svcUsed")
        model.add_node(svcUsesDB)
        model.add_node(svcUsedByDB)
        model.add_interaction(source_node=svcUsesDB, target_node=databaseNode)
        model.add_interaction(source_node=databaseNode, target_node=svcUsedByDB)

        extender: KubeExtender = KubeExtender(worker_list=[DatabaseWorker()])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        # Check that Service node had been converted to Database
        self.assertTrue(isinstance(list(model.nodes)[0], Datastore))

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

        # Check that Service node had been converted to Database
        self.assertFalse(isinstance(list(model.nodes)[0], Datastore))

    def test_database_double_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_TWO_CONTAINER)

        # Change pod port
        container_to_change: KContainer = pod.get_containers()[0]
        for port in container_to_change.ports:
            port["containerPort"] = 3306

        cluster.add_object(pod, KObjectKind.POD)

        model.add_node(Service(pod.metadata.name))

        extender: KubeExtender = KubeExtender(worker_list=[DatabaseWorker()])
        extender.extend(model, cluster)

        # Check nodes present
        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        # Check that Service node had been converted to Database
        self.assertTrue(isinstance(list(model.nodes)[0], Datastore))
