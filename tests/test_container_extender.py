from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Edge

from project.extender.extender import KubeExtender
from project.extender.workerimpl.container_worker import ContainerWorker
from project.kmodel.kCluster import KCluster
from data.kube_objects_dict import POD_WITH_ONE_CONTAINER

from project.kmodel.kPod import KPod
from project.kmodel.kobject_kind import KObjectKind


class TestContainerExtender(TestCase):

    def test_nothing_set(self):
        model = MicroToscaModel(name="container-test-model")
        model.add_group(Edge("edge"))
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        pod.spec.containers[0].ports[0]["host_port"] = None

        cluster.add_object(pod, KObjectKind.POD)

        svc_node = Service(pod.get_containers()[0].name + "." + pod.get_fullname())
        model.add_node(svc_node)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.get_all_objects()), 1)
        self.assertTrue(svc_node not in model.edge)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.get_all_objects()), 1)
        self.assertTrue(svc_node not in model.edge)

    def test_host_network_true(self):
        model = MicroToscaModel(name="container-test-model")
        model.add_group(Edge("edge"))
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        pod.spec.host_network = True

        cluster.add_object(pod, KObjectKind.POD)

        svc_node = Service(pod.get_containers()[0].name + "." + pod.get_fullname())
        model.add_node(svc_node)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.get_all_objects()), 1)
        self.assertTrue(svc_node not in model.edge)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.get_all_objects()), 1)
        self.assertTrue(svc_node in model.edge)

    def test_host_port(self):
        model = MicroToscaModel(name="container-test-model")
        model.add_group(Edge("edge"))
        cluster = KCluster()

        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        pod.spec.containers[0].ports[0]["host_port"] = 8080

        cluster.add_object(pod, KObjectKind.POD)

        svc_node = Service(pod.get_containers()[0].name + "." + pod.get_fullname())
        model.add_node(svc_node)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.get_all_objects()), 1)
        self.assertTrue(svc_node not in model.edge)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.get_all_objects()), 1)
        self.assertTrue(svc_node in model.edge)
