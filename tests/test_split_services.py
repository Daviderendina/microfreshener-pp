from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service
from microfreshener.core.model.nodes import Compute

from project.analyser.smell import MultipleServicesInOneContainerSmell
from project.kmodel.kCluster import KCluster
from project.kmodel.kDeployment import KDeployment
from project.kmodel.kPod import KPod

from data.kube_objects_dict import POD_WITH_TWO_CONTAINER, DEPLOYMENT_WITH_TWO_CONTAINER
from project.kmodel.kobject_kind import KObjectKind
from project.solver.solver import SplitServicesRefactoring


class TestSplitServices(TestCase):

    def test_pod_with_two_containers(self):
        model = MicroToscaModel("model")
        cluster = KCluster()

        k_pod = KPod.from_dict(POD_WITH_TWO_CONTAINER)
        cluster.add_object(k_pod, KObjectKind.POD)

        node_svc_name_1 = k_pod.get_containers()[0].name + "." + k_pod.get_name_dot_namespace()
        node_svc_1 = Service(node_svc_name_1)
        node_svc_name_2 = k_pod.get_containers()[1].name + "." + k_pod.get_name_dot_namespace()
        node_svc_2 = Service(node_svc_name_2)
        model.add_node(node_svc_1)
        model.add_node(node_svc_2)

        node_compute = Compute(k_pod.get_name_dot_namespace())
        model.add_node(node_compute)

        r1 = model.add_deployed_on(source_node=node_svc_1, target_node=node_compute)
        r2 = model.add_deployed_on(source_node=node_svc_2, target_node=node_compute)

        smell = MultipleServicesInOneContainerSmell(node=node_compute)
        smell.addNodeCause(node_svc_1)
        smell.addNodeCause(node_svc_2)
        smell.addLinkCause(r1)
        smell.addLinkCause(r2)

        self.assertEqual(len(cluster.get_all_objects()), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        # Run solver
        solver: SplitServicesRefactoring = SplitServicesRefactoring(model, cluster)
        solver.apply(smell)

        # Test solver output
        self.assertEqual(len(cluster.get_all_objects()), 2)
        self.assertEqual(len(list(model.nodes)), 3)
        pods = cluster.get_objects_by_kind(KObjectKind.POD)

        for pod in pods:
            self.assertEqual(len(pod.get_containers()), 1)

        self.assertTrue(pods[0].get_name_dot_namespace().endswith("_1.default"))
        self.assertTrue(pods[1].get_name_dot_namespace().endswith("_2.default"))
        self.assertEqual(pods[0].get_containers()[0].name, k_pod.get_containers()[0].name)
        self.assertEqual(pods[1].get_containers()[0].name, k_pod.get_containers()[1].name)

    def test_deploy_with_two_containers(self):
        model = MicroToscaModel("model")
        cluster = KCluster()

        k_deploy = KDeployment.from_dict(DEPLOYMENT_WITH_TWO_CONTAINER)
        cluster.add_object(k_deploy, KObjectKind.DEPLOYMENT)

        node_svc_name_1 = k_deploy.get_containers()[0].name + "." + k_deploy.get_name_dot_namespace()
        node_svc_1 = Service(node_svc_name_1)
        node_svc_name_2 = k_deploy.get_containers()[1].name + "." + k_deploy.get_name_dot_namespace()
        node_svc_2 = Service(node_svc_name_2)
        model.add_node(node_svc_1)
        model.add_node(node_svc_2)

        node_compute = Compute(k_deploy.get_name_dot_namespace())
        model.add_node(node_compute)

        r1 = model.add_deployed_on(source_node=node_svc_1, target_node=node_compute)
        r2 = model.add_deployed_on(source_node=node_svc_2, target_node=node_compute)

        smell = MultipleServicesInOneContainerSmell(node=node_compute)
        smell.addNodeCause(node_svc_1)
        smell.addNodeCause(node_svc_2)
        smell.addLinkCause(r1)
        smell.addLinkCause(r2)

        self.assertEqual(len(cluster.get_all_objects()), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        # Run solver
        solver: SplitServicesRefactoring = SplitServicesRefactoring(model, cluster)
        solver.apply(smell)

        # Test solver output
        self.assertEqual(len(cluster.get_all_objects()), 2)
        self.assertEqual(len(list(model.nodes)), 3)
        deployments = cluster.get_objects_by_kind(KObjectKind.DEPLOYMENT)

        for deploy in deployments:
            self.assertEqual(len(deploy.get_containers()), 1)

        self.assertTrue(deployments[0].get_name_dot_namespace().endswith("_1.default"))
        self.assertTrue(deployments[1].get_name_dot_namespace().endswith("_2.default"))
        self.assertEqual(deployments[0].get_containers()[0].name, k_deploy.get_containers()[0].name)
        self.assertEqual(deployments[1].get_containers()[0].name, k_deploy.get_containers()[1].name)