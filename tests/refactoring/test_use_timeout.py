import copy
from unittest import TestCase

from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import MF_VIRTUALSERVICE_TIMEOUT_NAME, MF_NAME_SUFFIX
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.kmodel.kube_workload import KubePod
from project.solver.impl.use_timeout_refactoring import UseTimeoutRefactoring


class TestRefactoringUseTimeout(TestCase):

    def test_add_timeout(self):
        model = MicroToscaModel("model")
        cluster = KubeCluster()

        # Create deploy objects
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_service = KubeService(copy.deepcopy(DEFAULT_SVC))

        cluster.add_object(k_pod)
        cluster.add_object(k_service)

        # Create model
        svc = Service(k_pod.containers[0].name + k_pod.fullname)
        mr = MessageRouter(k_service.fullname)

        model.add_node(svc)
        model.add_node(mr)
        r = model.add_interaction(source_node=svc, target_node=mr)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertEqual(len(cluster.virtual_services), 0)

        # Create smell
        smell = WobblyServiceInteractionSmell(svc)
        smell.addLinkCause(r)

        # Run solver
        solver: UseTimeoutRefactoring = UseTimeoutRefactoring(cluster, model)
        solver.apply(smell)

        # Check result
        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertEqual(len(cluster.virtual_services), 1)
        self.assertTrue(r.timeout)

        virtual_svc = cluster.virtual_services[0]

        self.assertEqual(virtual_svc.fullname, f"{k_service.name}-{MF_VIRTUALSERVICE_TIMEOUT_NAME}-{MF_NAME_SUFFIX}.{k_service.namespace}")
        self.assertListEqual(virtual_svc.hosts, [k_service.fullname])
        self.assertEqual(virtual_svc.destinations[0], k_service.fullname)
        self.assertEqual(virtual_svc.timeouts[0][2], f"{UseTimeoutRefactoring.DEFAULT_TIMEOUT_SEC}s")