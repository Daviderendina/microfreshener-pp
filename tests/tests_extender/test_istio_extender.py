import copy
from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, MessageRouter, Edge

from project.extender.extender import KubeExtender
from project.extender.workerimpl.istio_worker import IstioWorker
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_istio import KubeVirtualService, KubeDestinationRule, KubeIstioGateway
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC
from tests.data.istio_objects_dict import VIRTUAL_SERVICE_TIMEOUT, DESTINATION_RULE_TIMEOUT, \
    DESTINATION_RULE_CIRCUIT_BREAKER, GATEWAY
from project.kmodel.kube_networking import KubeService
from project.kmodel.kube_workload import KubePod


class TestIstioExtender(TestCase):

    # TEST TIMEOUT

    def test_timeout_virtual_service_pod_service(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KubeCluster()

        # Kubernetes
        k_service = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_1.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_2.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_1.data["metadata"]["name"] = k_pod_1.data["metadata"]["name"]  + "_1"
        k_pod_2.data["metadata"]["name"] = k_pod_2.data["metadata"]["name"]  + "_2"

        k_virtualservice = KubeVirtualService(VIRTUAL_SERVICE_TIMEOUT)
        k_virtualservice.data.get("spec", {}).get("hosts", []) \
            .append(k_service.fullname + ".svc.cluster.local")
        k_virtualservice.data["spec"]["http"][0]["route"][0]["destination"]["host"] = \
            k_service.fullname + ".svc.cluster.local"

        cluster.add_object(k_service)
        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_virtualservice)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.fullname)
        service_node_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.fullname)
        mr_node = MessageRouter(k_service.fullname + ".svc.cluster.local")
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(mr_node)
        model.add_interaction(source_node=service_node_1, target_node=mr_node)
        model.add_interaction(source_node=service_node_2, target_node=mr_node)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(mr_node.incoming_interactions[0].timeout)
        self.assertFalse(mr_node.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(mr_node.interactions), 0)
        self.assertEqual(len(mr_node.incoming_interactions), 2)
        self.assertTrue(mr_node.incoming_interactions[0].timeout)
        self.assertTrue(mr_node.incoming_interactions[1].timeout)

    def test_timeout_virtual_service_pod_pod(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KubeCluster()

        # Kubernetes
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_3 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_1.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_2.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_3.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_1.data["metadata"]["name"] = k_pod_1.data["metadata"]["name"] + "_1"
        k_pod_2.data["metadata"]["name"] = k_pod_2.data["metadata"]["name"] + "_2"
        k_pod_3.data["metadata"]["name"] = k_pod_3.data["metadata"]["name"] + "_3"

        k_container_3_name = k_pod_3.containers[0].name + "." + k_pod_3.fullname
        k_virtualservice = KubeVirtualService(VIRTUAL_SERVICE_TIMEOUT)
        k_virtualservice.data.get("spec", {}).get("hosts", []).append(k_container_3_name)
        k_virtualservice.data["spec"]["http"][0]["route"][0]["destination"]["host"] = k_container_3_name

        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_pod_3)
        cluster.add_object(k_virtualservice)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.fullname)
        service_node_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.fullname)
        service_node_3 = Service(k_pod_3.containers[0].name + "." + k_pod_3.fullname)
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(service_node_3)
        model.add_interaction(source_node=service_node_1, target_node=service_node_3)
        model.add_interaction(source_node=service_node_2, target_node=service_node_3)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(service_node_3.incoming_interactions[0].timeout)
        self.assertFalse(service_node_3.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(service_node_3.interactions), 0)
        self.assertEqual(len(service_node_3.incoming_interactions), 2)
        self.assertTrue(service_node_3.incoming_interactions[0].timeout)
        self.assertTrue(service_node_3.incoming_interactions[1].timeout)

    def test_timeout_destination_rule_pod_service(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KubeCluster()

        # Kubernetes
        k_service = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_1.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_2.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_1.data["metadata"]["name"] = k_pod_1.data["metadata"]["name"] + "_1"
        k_pod_2.data["metadata"]["name"] = k_pod_2.data["metadata"]["name"] + "_2"

        k_destinationrule = KubeDestinationRule(DESTINATION_RULE_TIMEOUT)
        k_destinationrule.data["spec"]["host"] = k_service.fullname + ".svc.cluster.local"

        cluster.add_object(k_service)
        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_destinationrule)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.fullname)
        service_node_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.fullname)
        mr_node = MessageRouter(k_service.fullname + ".svc.cluster.local")
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(mr_node)
        model.add_interaction(source_node=service_node_1, target_node=mr_node)
        model.add_interaction(source_node=service_node_2, target_node=mr_node)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(mr_node.incoming_interactions[0].timeout)
        self.assertFalse(mr_node.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(mr_node.interactions), 0)
        self.assertEqual(len(mr_node.incoming_interactions), 2)
        self.assertTrue(mr_node.incoming_interactions[0].timeout)
        self.assertTrue(mr_node.incoming_interactions[1].timeout)

    def test_timeout_destination_rule_pod_pod(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KubeCluster()

        # Kubernetes
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_3 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_1.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_2.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_3.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_1.data["metadata"]["name"] = k_pod_1.data["metadata"]["name"] + "_1"
        k_pod_2.data["metadata"]["name"] = k_pod_2.data["metadata"]["name"] + "_2"
        k_pod_3.data["metadata"]["name"] = k_pod_3.data["metadata"]["name"] + "_3"

        k_container_3_name = k_pod_3.containers[0].name + "." + k_pod_3.fullname
        k_destinationrule = KubeDestinationRule(DESTINATION_RULE_TIMEOUT)
        k_destinationrule.data["spec"]["host"] = k_container_3_name

        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_pod_3)
        cluster.add_object(k_destinationrule)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.fullname)
        service_node_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.fullname)
        service_node_3 = Service(k_pod_3.containers[0].name + "." + k_pod_3.fullname)
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(service_node_3)
        model.add_interaction(source_node=service_node_1, target_node=service_node_3)
        model.add_interaction(source_node=service_node_2, target_node=service_node_3)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(service_node_3.incoming_interactions[0].timeout)
        self.assertFalse(service_node_3.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(service_node_3.interactions), 0)
        self.assertEqual(len(service_node_3.incoming_interactions), 2)
        self.assertTrue(service_node_3.incoming_interactions[0].timeout)
        self.assertTrue(service_node_3.incoming_interactions[1].timeout)

    # TEST GATEWAY

    def test_gateway_found(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        gateway_vs_host = "*.bookinfo.com"

        label = {'app': 'test'}

        # Kubernetes
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod.data["metadata"]["labels"] = label

        k_service = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_service.data["spec"]["selector"] = label

        k_virtualservice = KubeVirtualService(copy.deepcopy(VIRTUAL_SERVICE_TIMEOUT))
        k_gateway = KubeIstioGateway(copy.deepcopy(GATEWAY))

        host_name = k_virtualservice.fullname  # TODO FQDN?
        k_gateway.data["spec"]["selectors"] = label
        k_gateway.data["spec"]["servers"][0]["hosts"] = [gateway_vs_host]

        k_virtualservice.data["spec"]["hosts"] = [gateway_vs_host.replace("*", "wildcard.test")]
        k_virtualservice.data["spec"]["gateways"] = [k_gateway.fullname]  # TODO FQDN?
        k_virtualservice.data["spec"]["http"][0]["route"][0]["destination"][
            "host"] = k_service.fullname  # TODO FQDN?

        cluster.add_object(k_pod)
        cluster.add_object(k_virtualservice)
        cluster.add_object(k_service)
        cluster.add_object(k_gateway)

        # TOSCA model
        svc_node = Service(k_pod.containers[0].name + "." + k_pod.fullname)
        mr_node = MessageRouter(k_service.fullname + ".svc.cluster.local")
        model.add_node(svc_node)
        model.add_node(mr_node)
        model.edge.add_member(mr_node)
        model.add_interaction(source_node=mr_node, target_node=svc_node)

        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(cluster.cluster_objects), 4)

        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len([n for n in model.nodes]), 3)
        self.assertEqual(len(cluster.cluster_objects), 4)

    # TEST CIRCUIT BREAKER

    def test_circuit_breaker_pod_pod(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KubeCluster()

        # Kubernetes
        data_1 = copy.deepcopy(POD_WITH_ONE_CONTAINER)
        data_2 = copy.deepcopy(POD_WITH_ONE_CONTAINER)
        data_3 = copy.deepcopy(POD_WITH_ONE_CONTAINER)
        data_1["metadata"]["labels"] = {'app': 'test'}
        data_2["metadata"]["labels"] = {'app': 'test'}
        data_3["metadata"]["labels"] = {'app': 'test'}
        data_1["metadata"]["name"] = data_1["metadata"]["name"] + "_1"
        data_2["metadata"]["name"] = data_2["metadata"]["name"] + "_2"
        data_3["metadata"]["name"] = data_3["metadata"]["name"] + "_3"

        k_pod_1 = KubePod(data_1)
        k_pod_2 = KubePod(data_2)
        k_pod_3 = KubePod(data_3)

        k_container_3_name = k_pod_3.containers[0].name + "." + k_pod_3.fullname
        k_destinationrule = KubeDestinationRule(DESTINATION_RULE_CIRCUIT_BREAKER)
        k_destinationrule.data["spec"]["host"] = k_container_3_name

        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_pod_3)
        cluster.add_object(k_destinationrule)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.fullname)
        service_node_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.fullname)
        service_node_3 = Service(k_pod_3.containers[0].name + "." + k_pod_3.fullname)
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(service_node_3)
        model.add_interaction(source_node=service_node_1, target_node=service_node_3)
        model.add_interaction(source_node=service_node_2, target_node=service_node_3)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(service_node_3.incoming_interactions[0].circuit_breaker)
        self.assertFalse(service_node_3.incoming_interactions[1].circuit_breaker)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(service_node_3.interactions), 0)
        self.assertEqual(len(service_node_3.incoming_interactions), 2)
        self.assertTrue(service_node_3.incoming_interactions[0].circuit_breaker)
        self.assertTrue(service_node_3.incoming_interactions[1].circuit_breaker)

    def test_circuit_breaker_pod_service(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KubeCluster()

        # Kubernetes
        k_service = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_1.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_2.data["metadata"]["labels"] = {'app': 'test'}
        k_pod_1.data["metadata"]["name"] = k_pod_1.data["metadata"]["name"] + "_1"
        k_pod_2.data["metadata"]["name"] = k_pod_2.data["metadata"]["name"] + "_2"

        k_destinationrule = KubeDestinationRule(DESTINATION_RULE_CIRCUIT_BREAKER)
        k_destinationrule.data["spec"]["host"] = k_service.fullname + ".svc.cluster.local"

        cluster.add_object(k_service)
        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_destinationrule)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.fullname)
        service_node_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.fullname)
        mr_node = MessageRouter(k_service.fullname + ".svc.cluster.local")
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(mr_node)
        model.add_interaction(source_node=service_node_1, target_node=mr_node)
        model.add_interaction(source_node=service_node_2, target_node=mr_node)

        # Check models
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(mr_node.incoming_interactions[0].circuit_breaker)
        self.assertFalse(mr_node.incoming_interactions[1].circuit_breaker)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(mr_node.interactions), 0)
        self.assertEqual(len(mr_node.incoming_interactions), 2)
        self.assertTrue(mr_node.incoming_interactions[0].circuit_breaker)
        self.assertTrue(mr_node.incoming_interactions[1].circuit_breaker)
