import copy
from unittest import TestCase

from microfreshener.core.analyser.smell import MultipleServicesInOneContainerSmell
from microfreshener.core.model import MicroToscaModel, Service
from microfreshener.core.model.nodes import Compute

from data.kube_objects_dict import POD_WITH_TWO_CONTAINER, DEPLOYMENT_WITH_TWO_CONTAINER
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_workload import KubePod, KubeDeployment
from project.solver.split_services_refactoring import SplitServicesRefactoring


class TestRefactoringSplitServices(TestCase):

    def test_pod_with_two_containers(self):
        model = MicroToscaModel("model")
        cluster = KubeCluster()

        k_pod = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        cluster.add_object(k_pod)

        node_svc_name_1 = k_pod.containers[0].name + "." + k_pod.fullname
        node_svc_1 = Service(node_svc_name_1)
        node_svc_name_2 = k_pod.containers[1].name + "." + k_pod.fullname
        node_svc_2 = Service(node_svc_name_2)
        model.add_node(node_svc_1)
        model.add_node(node_svc_2)

        node_compute = Compute(k_pod.fullname)
        model.add_node(node_compute)

        r1 = model.add_deployed_on(source_node=node_svc_1, target_node=node_compute)
        r2 = model.add_deployed_on(source_node=node_svc_2, target_node=node_compute)

        smell = MultipleServicesInOneContainerSmell(node=node_compute)
        smell.addNodeCause(node_svc_1)
        smell.addNodeCause(node_svc_2)
        smell.addLinkCause(r1)
        smell.addLinkCause(r2)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        # Run solver
        solver: SplitServicesRefactoring = SplitServicesRefactoring(cluster)
        solver.apply(smell)

        # Test solver output
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 3)

        pods = [p for p in cluster.workloads if isinstance(p, KubePod)]
        for pod in pods:
            self.assertEqual(len(pod.containers), 1)

        self.assertTrue(pods[0].fullname.endswith("_1.default"))
        self.assertTrue(pods[1].fullname.endswith("_2.default"))
        self.assertEqual(pods[0].containers[0].name, k_pod.containers[0].name)
        self.assertEqual(pods[1].containers[0].name, k_pod.containers[1].name)

    def test_deploy_with_two_containers(self):
        model = MicroToscaModel("model")
        cluster = KubeCluster()

        k_deploy = KubeDeployment(DEPLOYMENT_WITH_TWO_CONTAINER)
        cluster.add_object(k_deploy)

        node_svc_name_1 = k_deploy.containers[0].name + "." + k_deploy.fullname
        node_svc_name_2 = k_deploy.containers[1].name + "." + k_deploy.fullname
        node_svc_1 = Service(node_svc_name_1)
        node_svc_2 = Service(node_svc_name_2)
        model.add_node(node_svc_1)
        model.add_node(node_svc_2)

        node_compute = Compute(k_deploy.fullname)
        model.add_node(node_compute)

        r1 = model.add_deployed_on(source_node=node_svc_1, target_node=node_compute)
        r2 = model.add_deployed_on(source_node=node_svc_2, target_node=node_compute)

        smell = MultipleServicesInOneContainerSmell(node=node_compute)
        smell.addNodeCause(node_svc_1)
        smell.addNodeCause(node_svc_2)
        smell.addLinkCause(r1)
        smell.addLinkCause(r2)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        # Run solver
        solver: SplitServicesRefactoring = SplitServicesRefactoring(cluster)
        solver.apply(smell)

        # Test solver output
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 3)
        deployments = [d for d in cluster.workloads if isinstance(d, KubeDeployment)]

        for deploy in deployments:
            self.assertEqual(len(deploy.containers), 1)

        self.assertTrue(deployments[0].fullname.endswith("_1.default"))
        self.assertTrue(deployments[1].fullname.endswith("_2.default"))
        self.assertEqual(deployments[0].containers[0].name, k_deploy.containers[0].name)
        self.assertEqual(deployments[1].containers[0].name, k_deploy.containers[1].name)