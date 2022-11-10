from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, MessageRouter, Datastore

from project.extender.extender import KubeExtender
from project.extender.kubeworker import ServiceWorker
from project.kmodel.kCluster import KCluster
from project.kmodel.kPod import KPod
from project.kmodel.kService import KService
from data.kube_objects_dict import DEFAULT_SVC, POD_WITH_ONE_CONTAINER

from project.kmodel.kobject_kind import KObjectKind


class TestServiceExtender(TestCase):

    '''
    Test case: a Kubernetes Service is represented as Service and not MessageRouter node type in the graph, the type
    of this graph is switched to MessageRouter and all relations are maintained
    '''
    def test_model_service_is_kubernetes_service(self):

        model = MicroToscaModel(name="service-model")
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)

        # Add Service to Tosca Model
        svc1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        svc2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        svc3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        mr = Service(k_svc.get_name_dot_namespace())
        model.add_node(svc1)
        model.add_node(svc2)
        model.add_node(svc3)
        model.add_node(mr)
        model.add_interaction(source_node=svc1, target_node=mr)
        model.add_interaction(source_node=svc2, target_node=mr)
        model.add_interaction(source_node=mr, target_node=svc3)

        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 4)

        extender: KubeExtender = KubeExtender(worker_list=[ServiceWorker()])
        extender.extend(model, cluster)

        count = 0
        for node in model.nodes:
            if isinstance(node, MessageRouter):
                count += 1
                mr = node
        self.assertEqual(count, 1)

        self.assertEqual(len(svc1.interactions), 1)
        self.assertEqual(len(svc1.incoming_interactions), 0)
        self.assertEqual(len(svc2.interactions), 1)
        self.assertEqual(len(svc2.incoming_interactions), 0)
        self.assertEqual(len(mr.interactions), 1)
        self.assertEqual(len(mr.incoming_interactions), 2)
        self.assertEqual(len(svc3.interactions), 0)
        self.assertEqual(len(svc3.incoming_interactions), 1)

        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 4)

    '''
    Test case: there is a direct communication between two pods but the service defined does not expone them.
    '''
    def test_message_router_not_found_in_model(self):
        model = MicroToscaModel(name="service-model")
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_svc.spec.selector = {'err':'err'}
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)

        # Add Service to Tosca Model
        svc1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        svc3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        model.add_node(svc1)
        model.add_node(svc3)
        model.add_interaction(source_node=svc1, target_node=svc3)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[ServiceWorker()])
        extender.extend(model, cluster)

        count = 0
        for node in model.nodes:
            if isinstance(node, MessageRouter):
                count += 1
        self.assertEqual(count, 0)

        self.assertEqual(len(svc1.interactions), 1)
        self.assertEqual(len(svc1.incoming_interactions), 0)
        self.assertEqual(len(svc3.interactions), 0)
        self.assertEqual(len(svc3.incoming_interactions), 1)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 2)

    '''
    Test case: the communication between two pods is direct, but there's in the K8s deploy a SVC between the pods
    '''
    def test_service_not_found(self):
        model = MicroToscaModel(name="service-model")
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)

        # Add Service to Tosca Model
        svc1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        svc2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        svc3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        model.add_node(svc1)
        model.add_node(svc2)
        model.add_node(svc3)
        model.add_interaction(source_node=svc1, target_node=svc3)
        model.add_interaction(source_node=svc2, target_node=svc3)

        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)

        extender: KubeExtender = KubeExtender(worker_list=[ServiceWorker()])
        extender.extend(model, cluster)

        count = 0
        for node in model.nodes:
            if isinstance(node, MessageRouter):
                count += 1
                mr = node
        self.assertEqual(count, 1)

        self.assertEqual(len(svc1.interactions), 1)
        self.assertEqual(len(svc1.incoming_interactions), 0)
        self.assertEqual(len(svc2.interactions), 1)
        self.assertEqual(len(svc2.incoming_interactions), 0)
        self.assertEqual(len(mr.interactions), 1)
        self.assertEqual(len(mr.incoming_interactions), 2)
        self.assertEqual(len(svc3.interactions), 0)
        self.assertEqual(len(svc3.incoming_interactions), 1)

        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 4)

    '''
    Test case: il MessageRouter è già presente
    '''
    def test_service_is_present(self):
        model = MicroToscaModel(name="service-model")
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)

        # Add Service to Tosca Model
        svc1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        svc3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        mr = MessageRouter(k_svc.get_name_dot_namespace())
        model.add_node(svc1)
        model.add_node(svc3)
        model.add_node(mr)
        model.add_interaction(source_node=svc1, target_node=mr)
        model.add_interaction(source_node=mr, target_node=svc3)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 3)

        extender: KubeExtender = KubeExtender(worker_list=[ServiceWorker()])
        extender.extend(model, cluster)

        count = 0
        for node in model.nodes:
            if isinstance(node, MessageRouter):
                count += 1
        self.assertEqual(count, 1)

        self.assertEqual(len(svc1.interactions), 1)
        self.assertEqual(len(svc1.incoming_interactions), 0)
        self.assertEqual(len(mr.interactions), 1)
        self.assertEqual(len(mr.incoming_interactions), 1)
        self.assertEqual(len(svc3.interactions), 0)
        self.assertEqual(len(svc3.incoming_interactions), 1)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 3)