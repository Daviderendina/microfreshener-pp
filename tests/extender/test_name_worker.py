import copy
from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from microfreshenerpp.extender.extender import KubeExtender
from microfreshenerpp.extender.worker_names import NAME_WORKER
from microfreshenerpp.kmodel.kube_cluster import KubeCluster
from microfreshenerpp.kmodel.kube_networking import KubeIngress, KubeService
from microfreshenerpp.kmodel.kube_workload import KubePod
from microfreshenerpp.kmodel.shortnames import KUBE_POD, KUBE_SERVICE, KUBE_INGRESS
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC_INGRESS, DEFAULT_SVC, \
    POD_WITH_TWO_CONTAINER


class TestNameWorker(TestCase):

    def test_service_pod(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_container = pod.containers[0]
        pod_2_container = pod_2.containers[0]

        pod_2.data["metadata"]["name"] = pod_2.data["metadata"]["name"] + "_2"
        cluster.add_object(pod)
        cluster.add_object(pod_2)

        # Model
        svc = Service(pod_container.fullname)
        svc_2 = Service(pod_2_container.typed_fullname)
        model.add_node(svc)
        model.add_node(svc_2)
        model.add_interaction(svc, svc_2)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender([NAME_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(svc.name, f"{pod_container.fullname}.{KUBE_POD}")
        self.assertEqual(svc_2.name, pod_2_container.typed_fullname)

    def test_service_name_is_pod_one_container(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_container = pod.containers[0]
        cluster.add_object(pod)

        # Model
        svc = Service(pod.fullname)
        model.add_node(svc)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        extender: KubeExtender = KubeExtender([NAME_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        self.assertEqual(svc.name, f"{pod_container.fullname}.{KUBE_POD}")

    def test_service_name_is_pod_two_container(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        pod = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        pod_container = pod.containers[0]
        cluster.add_object(pod)

        # Model
        svc = Service(pod.fullname)
        model.add_node(svc)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        error = False
        try:
            extender: KubeExtender = KubeExtender([NAME_WORKER])
            extender.extend(model, cluster)
        except:
            error = True

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        self.assertTrue(error)


    def test_service_name_with_type(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_container = pod.containers[0]
        pod_2_container = pod_2.containers[0]

        pod.data["metadata"]["name"] = pod.data["metadata"]["name"] + ".pod"
        pod_2.data["metadata"]["name"] = pod_2.data["metadata"]["name"] + "_2"
        cluster.add_object(pod)
        cluster.add_object(pod_2)

        # Model
        svc = Service(pod_container.fullname)
        svc_2 = Service(pod_2_container.typed_fullname)
        model.add_node(svc)
        model.add_node(svc_2)
        model.add_interaction(svc, svc_2)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender([NAME_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(svc.name, f"{pod_container.fullname}.{KUBE_POD}")
        self.assertEqual(svc_2.name, pod_2_container.typed_fullname)

    def test_message_routers(self):
        model = MicroToscaModel("test_message_routers")
        cluster = KubeCluster()

        # Cluster
        k_ingress = KubeIngress(copy.deepcopy(DEFAULT_SVC_INGRESS))
        k_service = KubeService(copy.deepcopy(DEFAULT_SVC))

        cluster.add_object(k_ingress)
        cluster.add_object(k_service)

        # Model
        mr_ing = MessageRouter(k_ingress.fullname)
        mr_svc = MessageRouter(k_service.fullname)
        model.add_node(mr_svc)
        model.add_node(mr_ing)
        model.add_interaction(mr_ing, mr_svc)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender([NAME_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(mr_ing.name, f"{k_ingress.fullname}.{KUBE_INGRESS}")
        self.assertEqual(mr_svc.name, f"{k_service.fullname}.{KUBE_SERVICE}")
