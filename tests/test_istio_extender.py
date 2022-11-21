from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, MessageRouter, Edge

from project.extender.extender import KubeExtender
from project.extender.workerimpl.istio_worker import IstioWorker
from project.kmodel.istio import VirtualService, DestinationRule, Gateway
from project.kmodel.kCluster import KCluster
from project.kmodel.kPod import KPod
from data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind
from data.istio_objects_dict import VIRTUAL_SERVICE_TIMEOUT, DESTINATION_RULE_TIMEOUT, DESTINATION_RULE_CIRCUIT_BREAKER, \
    GATEWAY


class TestIstioExtender(TestCase):

    # TEST TIMEOUT

    def test_timeout_virtual_service_pod_service(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KCluster()

        # Kubernetes
        k_service = KService.from_dict(DEFAULT_SVC)
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_1.metadata.labels = {'app': 'test'}
        k_pod_2.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"

        k_virtualservice = VirtualService(VIRTUAL_SERVICE_TIMEOUT)
        k_virtualservice.data.get("spec", {}).get("hosts", []) \
            .append(k_service.get_name_dot_namespace() + ".svc.cluster.local")
        k_virtualservice.data["spec"]["http"][0]["route"][0]["destination"]["host"] = \
            k_service.get_name_dot_namespace() + ".svc.cluster.local"

        cluster.add_object(k_service, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_virtualservice, KObjectKind.ISTIO_VIRTUAL_SERVICE)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        service_node_2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        mr_node = MessageRouter(k_service.get_name_dot_namespace() + ".svc.cluster.local")
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(mr_node)
        model.add_interaction(source_node=service_node_1, target_node=mr_node)
        model.add_interaction(source_node=service_node_2, target_node=mr_node)

        # Check models
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(mr_node.incoming_interactions[0].timeout)
        self.assertFalse(mr_node.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.get_all_objects()), 4)
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
        cluster = KCluster()

        # Kubernetes
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_1.metadata.labels = {'app': 'test'}
        k_pod_2.metadata.labels = {'app': 'test'}
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"

        k_container_3_name = k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace()
        k_virtualservice = VirtualService(VIRTUAL_SERVICE_TIMEOUT)
        k_virtualservice.data.get("spec", {}).get("hosts", []).append(k_container_3_name)
        k_virtualservice.data["spec"]["http"][0]["route"][0]["destination"]["host"] = k_container_3_name

        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)
        cluster.add_object(k_virtualservice, KObjectKind.ISTIO_VIRTUAL_SERVICE)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        service_node_2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        service_node_3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(service_node_3)
        model.add_interaction(source_node=service_node_1, target_node=service_node_3)
        model.add_interaction(source_node=service_node_2, target_node=service_node_3)

        # Check models
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(service_node_3.incoming_interactions[0].timeout)
        self.assertFalse(service_node_3.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.get_all_objects()), 4)
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
        cluster = KCluster()

        # Kubernetes
        k_service = KService.from_dict(DEFAULT_SVC)
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_1.metadata.labels = {'app': 'test'}
        k_pod_2.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"

        k_destinationrule = DestinationRule(DESTINATION_RULE_TIMEOUT)
        k_destinationrule.data["spec"]["host"] = k_service.get_name_dot_namespace() + ".svc.cluster.local"

        cluster.add_object(k_service, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_destinationrule, KObjectKind.ISTIO_DESTINATION_RULE)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        service_node_2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        mr_node = MessageRouter(k_service.get_name_dot_namespace() + ".svc.cluster.local")
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(mr_node)
        model.add_interaction(source_node=service_node_1, target_node=mr_node)
        model.add_interaction(source_node=service_node_2, target_node=mr_node)

        # Check models
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(mr_node.incoming_interactions[0].timeout)
        self.assertFalse(mr_node.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.get_all_objects()), 4)
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
        cluster = KCluster()

        # Kubernetes
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_1.metadata.labels = {'app': 'test'}
        k_pod_2.metadata.labels = {'app': 'test'}
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"

        k_container_3_name = k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace()
        k_destinationrule = DestinationRule(DESTINATION_RULE_TIMEOUT)
        k_destinationrule.data["spec"]["host"] = k_container_3_name

        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)
        cluster.add_object(k_destinationrule, KObjectKind.ISTIO_DESTINATION_RULE)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        service_node_2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        service_node_3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(service_node_3)
        model.add_interaction(source_node=service_node_1, target_node=service_node_3)
        model.add_interaction(source_node=service_node_2, target_node=service_node_3)

        # Check models
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(service_node_3.incoming_interactions[0].timeout)
        self.assertFalse(service_node_3.incoming_interactions[1].timeout)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.get_all_objects()), 4)
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
        # TODO
        pass
        # Vedere lo schema nella galleria del telefono, che spiega un po' quali siano gli attori in gioco per un
        # gateway e le relazioni. In particolare, le frecce grosse rappresentano il flusso della comunicazione tra gli
        # oggetti mentre quelle piccole il matching che ci deve essere tra i vari attributi degli stessi

        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge"))
        cluster = KCluster()

        label = {'app': 'test'}

        # Kubernetes

        k_pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod.metadata.labels = label

        k_service = KService.from_dict(DEFAULT_SVC)
        k_service.spec.selector = label

        k_virtualservice = VirtualService.from_dict(VIRTUAL_SERVICE_TIMEOUT)
        k_gateway = Gateway.from_dict(GATEWAY)

        host_name = k_virtualservice.get_name_dot_namespace()  # TODO FQDN?
        k_gateway.data["spec"]["selectors"] = label
        k_gateway.data["spec"]["servers"][0]["hosts"] = [host_name]

        k_virtualservice.data["spec"]["hosts"] = [host_name]
        k_virtualservice.data["spec"]["gateways"] = [k_gateway.get_name_dot_namespace()]  # TODO FQDN?
        k_virtualservice.data["spec"]["http"][0]["route"][0]["destination"][
            "host"] = k_service.get_name_dot_namespace()  # TODO FQDN?

        cluster.add_object(k_pod, KObjectKind.POD)
        cluster.add_object(k_virtualservice, KObjectKind.ISTIO_VIRTUAL_SERVICE)
        cluster.add_object(k_service, KObjectKind.SERVICE)
        cluster.add_object(k_gateway, KObjectKind.ISTIO_GATEWAY)

        # TOSCA model
        svc_node = Service(k_pod.get_containers()[0].name + "." + k_pod.get_name_dot_namespace())
        mr_node = MessageRouter(k_service.get_name_dot_namespace() + ".svc.cluster.local")
        model.add_node(svc_node)
        model.add_node(mr_node)
        model.edge.add_member(mr_node)
        model.add_interaction(source_node=mr_node, target_node=svc_node)

        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(cluster.get_all_objects()), 4)

        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len([n for n in model.nodes]), 3)
        self.assertEqual(len(cluster.get_all_objects()), 4)

    # TEST CIRCUIT BREAKER

    def test_circuit_breaker_pod_pod(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge("edge-group"))
        cluster = KCluster()

        # Kubernetes
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_1.metadata.labels = {'app': 'test'}
        k_pod_2.metadata.labels = {'app': 'test'}
        k_pod_3.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"
        k_pod_3.metadata.name = k_pod_3.metadata.name + "_3"

        k_container_3_name = k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace()
        k_destinationrule = DestinationRule(DESTINATION_RULE_CIRCUIT_BREAKER)
        k_destinationrule.data["spec"]["host"] = k_container_3_name

        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)
        cluster.add_object(k_destinationrule, KObjectKind.ISTIO_DESTINATION_RULE)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        service_node_2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        service_node_3 = Service(k_pod_3.get_containers()[0].name + "." + k_pod_3.get_name_dot_namespace())
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(service_node_3)
        model.add_interaction(source_node=service_node_1, target_node=service_node_3)
        model.add_interaction(source_node=service_node_2, target_node=service_node_3)

        # Check models
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(service_node_3.incoming_interactions[0].circuit_breaker)
        self.assertFalse(service_node_3.incoming_interactions[1].circuit_breaker)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.get_all_objects()), 4)
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
        cluster = KCluster()

        # Kubernetes
        k_service = KService.from_dict(DEFAULT_SVC)
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_1.metadata.labels = {'app': 'test'}
        k_pod_2.metadata.labels = {'app': 'test'}
        k_pod_1.metadata.name = k_pod_1.metadata.name + "_1"
        k_pod_2.metadata.name = k_pod_2.metadata.name + "_2"

        k_destinationrule = DestinationRule(DESTINATION_RULE_CIRCUIT_BREAKER)
        k_destinationrule.data["spec"]["host"] = k_service.get_name_dot_namespace() + ".svc.cluster.local"

        cluster.add_object(k_service, KObjectKind.SERVICE)
        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_destinationrule, KObjectKind.ISTIO_DESTINATION_RULE)

        # MicroToscaModel
        service_node_1 = Service(k_pod_1.get_containers()[0].name + "." + k_pod_1.get_name_dot_namespace())
        service_node_2 = Service(k_pod_2.get_containers()[0].name + "." + k_pod_2.get_name_dot_namespace())
        mr_node = MessageRouter(k_service.get_name_dot_namespace() + ".svc.cluster.local")
        model.add_node(service_node_1)
        model.add_node(service_node_2)
        model.add_node(mr_node)
        model.add_interaction(source_node=service_node_1, target_node=mr_node)
        model.add_interaction(source_node=service_node_2, target_node=mr_node)

        # Check models
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(mr_node.incoming_interactions[0].circuit_breaker)
        self.assertFalse(mr_node.incoming_interactions[1].circuit_breaker)

        # Run extender
        extender: KubeExtender = KubeExtender(worker_list=[IstioWorker()])
        extender.extend(model, cluster)

        # Check results
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertEqual(len(service_node_1.interactions), 1)
        self.assertEqual(len(service_node_1.incoming_interactions), 0)
        self.assertEqual(len(service_node_2.interactions), 1)
        self.assertEqual(len(service_node_2.incoming_interactions), 0)
        self.assertEqual(len(mr_node.interactions), 0)
        self.assertEqual(len(mr_node.incoming_interactions), 2)
        self.assertTrue(mr_node.incoming_interactions[0].circuit_breaker)
        self.assertTrue(mr_node.incoming_interactions[1].circuit_breaker)
