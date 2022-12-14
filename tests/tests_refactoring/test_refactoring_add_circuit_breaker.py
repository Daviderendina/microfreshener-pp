import copy
from unittest import TestCase

from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import MF_NAME_SUFFIX, MF_CIRCUITBREAKER_NAME
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.kmodel.kube_workload import KubePod
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC
from project.solver.add_circuit_breaker_refactoring import AddCircuitBreakerRefactoring


class TestRefactoringAddCircuitBreaker(TestCase):

    def _set_circuit_breaker_config(self):
        from config.kube_config import CIRCUIT_BREAKER_CONFIG
        CIRCUIT_BREAKER_CONFIG.MAX_CONNECTIONS = 1
        CIRCUIT_BREAKER_CONFIG.MAX_CONNECTIONS = 1
        CIRCUIT_BREAKER_CONFIG.HTTP_1_MAX_PENDING_REQUESTS = 1
        CIRCUIT_BREAKER_CONFIG.MAX_REQUESTS_PER_CONNECTION = 1
        CIRCUIT_BREAKER_CONFIG.CONSECUTIVE_5XX_ERRORS = 1
        CIRCUIT_BREAKER_CONFIG.INTERVAL = "1s"
        CIRCUIT_BREAKER_CONFIG.BASE_EJECTION_TIME = "3m"
        CIRCUIT_BREAKER_CONFIG.MAX_EJECTION_PERCENT = 1

    def test_add_circuit_breaker_for_service(self):
        model = MicroToscaModel("test_add_circuit_breaker_for_service")
        cluster = KubeCluster()

        # Populate cluster
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_service = KubeService(DEFAULT_SVC)

        cluster.add_object(k_pod)
        cluster.add_object(k_service)

        # Populate model
        service = Service(f"{k_pod.containers[0].name}.{k_pod.fullname}")
        messagerouter = MessageRouter(k_service.fullname)

        model.add_node(service)
        model.add_node(messagerouter)
        r = model.add_interaction(source_node=service, target_node=messagerouter)

        # Set up configuration for circuit breaker
        self._set_circuit_breaker_config()

        # Create smell
        smell = WobblyServiceInteractionSmell(service)
        smell.addLinkCause(r)

        # Check model and cluster
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertEqual(len(cluster.cluster_objects), 2)

        # Run solver
        solver: AddCircuitBreakerRefactoring = AddCircuitBreakerRefactoring(cluster)
        solver.apply(smell)

        # Check model and cluster
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(cluster.destination_rules), 1)

        # Check destination rule (circuit breaker) created
        circuit_breaker = cluster.destination_rules[0]
        self.assertEqual(circuit_breaker.name, f"{k_service.fullname}-{MF_CIRCUITBREAKER_NAME}-{MF_NAME_SUFFIX}")
        self.assertEqual(circuit_breaker.host, k_service.fullname)

        circuit_breaker_dict = circuit_breaker.data
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["connectionPool"]["tcp"].get("maxConnections", None))
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["connectionPool"]["http"].get("http1MaxPendingRequests", None))
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["connectionPool"]["http"].get("maxRequestsPerConnection", None))
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["outlierDetection"].get("interval", None))
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["outlierDetection"].get("consecutive5xxErrors", None))
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["outlierDetection"].get("baseEjectionTime", None))
        self.assertIsNotNone(circuit_breaker_dict["spec"]["trafficPolicy"]["outlierDetection"].get("maxEjectionPercent", None))




