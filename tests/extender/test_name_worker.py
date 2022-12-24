import copy
from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from project.extender.extender import KubeExtender
from project.extender.impl.name_worker import NameWorker
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeIngress, KubeService
from project.kmodel.kube_workload import KubePod, KubeDeployment
from project.kmodel.shortnames import KUBE_POD, KUBE_DEPLOYMENT, KUBE_SERVICE, KUBE_INGRESS
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEPLOYMENT_WITH_ONE_CONTAINER, DEFAULT_SVC_INGRESS, \
    DEFAULT_SVC


class TestNameWorker(TestCase):

    def test_service_pod(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_2.data["metadata"]["name"] = pod_2.data["metadata"]["name"] + "_2"
        cluster.add_object(pod)
        cluster.add_object(pod_2)

        # Model
        svc = Service(pod.fullname)
        svc_2 = Service(pod_2.typed_fullname)
        model.add_node(svc)
        model.add_node(svc_2)
        model.add_interaction(svc, svc_2)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[NameWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(list(model.nodes)[0].name, f"{pod.fullname}.{KUBE_POD}")

    def test_service_name_with_type(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod.data["metadata"]["name"] + ".pod"
        pod_2.data["metadata"]["name"] = pod_2.data["metadata"]["name"] + "_2"
        cluster.add_object(pod)
        cluster.add_object(pod_2)

        # Model
        svc = Service(pod.fullname)
        svc_2 = Service(pod_2.typed_fullname)
        model.add_node(svc)
        model.add_node(svc_2)
        model.add_interaction(svc, svc_2)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[NameWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(list(model.nodes)[0].name, f"{pod.fullname}.{KUBE_POD}")

    def test_service_deployment(self):
        model = MicroToscaModel("test_service")
        cluster = KubeCluster()

        # Cluster
        deploy = KubeDeployment(copy.deepcopy(DEPLOYMENT_WITH_ONE_CONTAINER))
        pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod_2.data["metadata"]["name"] = pod_2.data["metadata"]["name"] + "_2.pod"
        cluster.add_object(deploy)
        cluster.add_object(pod_2)

        # Model
        svc = Service(deploy.fullname)
        svc_2 = Service(pod_2.typed_fullname)
        model.add_node(svc)
        model.add_node(svc_2)
        model.add_interaction(svc, svc_2)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[NameWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(list(model.nodes)[0].name, f"{deploy.fullname}.{KUBE_DEPLOYMENT}")
        self.assertEqual(list(model.nodes)[1].name, pod_2.typed_fullname)

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

        extender: KubeExtender = KubeExtender(worker_list=[NameWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        self.assertEqual(mr_ing.name, f"{k_ingress.fullname}.{KUBE_INGRESS}")
        self.assertEqual(mr_svc.name, f"{k_service.fullname}.{KUBE_SERVICE}")
