import copy
from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Edge

from project.extender.extender import KubeExtender
from project.extender.impl.container_worker import ContainerWorker
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_workload import KubePod


class TestContainerExtender(TestCase):

    def test_nothing_set(self):
        model = MicroToscaModel(name="container-test-model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["spec"]["hostNetwork"] = False
        pod.data["spec"]["containers"][0]["ports"][0]["host_port"] = None

        cluster.add_object(pod)

        svc_node = Service(pod.containers[0].name + "." + pod.fullname)
        model.add_node(svc_node)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.cluster_objects), 1)
        self.assertTrue(svc_node not in model.edge)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.cluster_objects), 1)
        self.assertTrue(svc_node not in model.edge)

    def test_host_network_true(self):
        model = MicroToscaModel(name="container-test-model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["spec"]["hostNetwork"] = True

        cluster.add_object(pod)

        svc_node = Service(pod.containers[0].name + "." + pod.fullname)
        model.add_node(svc_node)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.cluster_objects), 1)
        self.assertTrue(svc_node not in model.edge)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.cluster_objects), 1)
        self.assertTrue(svc_node in model.edge)

    def test_host_port(self):
        model = MicroToscaModel(name="container-test-model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["spec"]["containers"][0]["ports"][0]["host_port"] = 8080

        cluster.add_object(pod)

        svc_node = Service(pod.containers[0].name + "." + pod.fullname)
        model.add_node(svc_node)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.cluster_objects), 1)
        self.assertTrue(svc_node not in model.edge)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertTrue(len([n for n in model.nodes]), 1)
        self.assertTrue(len(cluster.cluster_objects), 1)
        self.assertTrue(svc_node in model.edge)
