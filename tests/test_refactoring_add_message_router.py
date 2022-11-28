from unittest import TestCase

from microfreshener.core.analyser.smell import EndpointBasedServiceInteractionSmell
from microfreshener.core.model import Service, MicroToscaModel, MessageRouter

from project.kmodel.kCluster import KCluster
from project.kmodel.kPod import KPod
from data.kube_objects_dict import POD_WITH_TWO_CONTAINER, POD_WITH_ONE_CONTAINER, DEFAULT_SVC
from project.kmodel.kService import KService

from project.kmodel.kobject_kind import KObjectKind
from project.solver.add_message_router_refactoring import AddMessageRouterRefactoring


class TestRefactoringAddMessageRouter(TestCase):

    def test_add_service_with_pod_resource(self):
        model = MicroToscaModel("model")
        cluster = KCluster()

        # Create pods for cluster
        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_TWO_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)

        k_pod_1.metadata.name = "pod_1"
        k_pod_2.metadata.name = "pod_2"
        k_pod_3.metadata.name = "pod_3"

        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)

        # Create TOSCA nodes
        node_svc_name_1 = k_pod_1.get_containers()[0].name + "." + k_pod_1.get_fullname()
        node_svc_name_2 = k_pod_2.get_containers()[0].name + "." + k_pod_2.get_fullname()
        node_svc_name_3 = k_pod_2.get_containers()[1].name + "." + k_pod_2.get_fullname()
        node_svc_name_4 = k_pod_3.get_containers()[0].name + "." + k_pod_3.get_fullname()

        node_svc_1 = Service(node_svc_name_1)
        node_svc_2 = Service(node_svc_name_2)
        node_svc_3 = Service(node_svc_name_3)
        node_svc_4 = Service(node_svc_name_4)

        model.add_node(node_svc_1)
        model.add_node(node_svc_2)
        model.add_node(node_svc_3)
        model.add_node(node_svc_4)

        r1 = model.add_interaction(source_node=node_svc_1, target_node=node_svc_4)
        r2 = model.add_interaction(source_node=node_svc_2, target_node=node_svc_4)
        r3 = model.add_interaction(source_node=node_svc_3, target_node=node_svc_4)

        smell = EndpointBasedServiceInteractionSmell(node=node_svc_4)

        smell.addLinkCause(r1)
        smell.addLinkCause(r2)
        smell.addLinkCause(r3)

        # Assert that everything had been created properly
        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(cluster.get_objects_by_kind(KObjectKind.SERVICE)), 0)

        # Run solver
        solver: AddMessageRouterRefactoring = AddMessageRouterRefactoring(model, cluster)
        solver.apply(smell)

        # Test solver output
        # Check cluster
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(cluster.get_objects_by_kind(KObjectKind.SERVICE)), 1)
        k_service = cluster.get_objects_by_kind(KObjectKind.SERVICE)[0]

        # Check name
        service_name = k_pod_3.metadata.name + AddMessageRouterRefactoring.svc_name_suffix
        service_ns = k_pod_3.get_namespace()
        self.assertEqual(k_service.get_fullname(), f"{service_name}.{service_ns}")

        # Check labels
        matching_labels = [l for l in k_service.get_selectors() if l in k_pod_3.get_labels()]
        self.assertEqual(len(matching_labels), 1)

        # Check ports
        # STRING_FORMAT: <NAME>_<PROTOCOL>_<PORT>_<TARGET_PORT>
        service_ports = []
        for sp in k_service.spec.ports:
            self.assertTrue({sp['name']})
            matching_port = sp.get('target_port', None) if sp.get('target_port', None) else sp.get('port', None)
            service_ports.append(f"{sp.get('protocol', 'PROTOCOL')}  {matching_port}")

        for container in k_pod_3.get_containers():
            for port in container.ports:
                port_str = f"{port.get('protocol', 'PROTOCOL')}  {port.get('containerPort','PORT')}"
                self.assertTrue(port_str in service_ports)

    def test_add_service_with_pod_resource_and_existing_service(self):
        model = MicroToscaModel("model")
        cluster = KCluster()

        # Create objects for cluster
        labels = {'test': 'test_add_service_with_pod_resource_and_existing_service'}

        k_pod_1 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod_2 = KPod.from_dict(POD_WITH_TWO_CONTAINER)
        k_pod_3 = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_service = KService.from_dict(DEFAULT_SVC)

        k_pod_1.metadata.name = "pod_1"
        k_pod_2.metadata.name = "pod_2"
        k_pod_3.metadata.name = "pod_3"
        k_pod_3.metadata.labels = labels
        k_service.spec.selector = labels
        k_service.spec.ports = [{'name': 'svc-port', 'port': 8081, 'protocol': 'TCP', 'targetPort': 8080}]

        cluster.add_object(k_pod_1, KObjectKind.POD)
        cluster.add_object(k_pod_2, KObjectKind.POD)
        cluster.add_object(k_pod_3, KObjectKind.POD)
        cluster.add_object(k_service, KObjectKind.SERVICE)

        # Create TOSCA nodes
        node_svc_name_1 = k_pod_1.get_containers()[0].name + "." + k_pod_1.get_fullname()
        node_svc_name_2 = k_pod_2.get_containers()[0].name + "." + k_pod_2.get_fullname()
        node_svc_name_3 = k_pod_2.get_containers()[1].name + "." + k_pod_2.get_fullname()
        node_svc_name_4 = k_pod_3.get_containers()[0].name + "." + k_pod_3.get_fullname()

        node_svc_1 = Service(node_svc_name_1)
        node_svc_2 = Service(node_svc_name_2)
        node_svc_3 = Service(node_svc_name_3)
        node_svc_4 = Service(node_svc_name_4)
        node_mr = MessageRouter(k_service.get_fullname())

        model.add_node(node_svc_1)
        model.add_node(node_svc_2)
        model.add_node(node_svc_3)
        model.add_node(node_svc_4)
        model.add_node(node_mr)

        r1 = model.add_interaction(source_node=node_svc_1, target_node=node_svc_4)
        r2 = model.add_interaction(source_node=node_svc_2, target_node=node_mr)
        r3 = model.add_interaction(source_node=node_svc_3, target_node=node_mr)
        r4 = model.add_interaction(source_node=node_mr, target_node=node_svc_4)

        smell = EndpointBasedServiceInteractionSmell(node=node_svc_4)
        smell.addLinkCause(r1)

        port_number = len(k_service.get_ports())

        # Assert that everything had been created properly
        self.assertEqual(len(cluster.get_all_objects()), 4)
        self.assertEqual(len(cluster.get_objects_by_kind(KObjectKind.SERVICE)), 1)
        self.assertEqual(port_number, 1)

        # Run solver
        solver: AddMessageRouterRefactoring = AddMessageRouterRefactoring(model, cluster)
        solver.apply(smell)

        # Test solver output
        # Check cluster
        self.assertEqual(len(cluster.get_objects_by_kind(KObjectKind.SERVICE)), 1)
        self.assertEqual(len(cluster.get_all_objects()), 4)
        k_service_retrieved = cluster.get_objects_by_kind(KObjectKind.SERVICE)[0]

        # Check name
        self.assertEqual(k_service, k_service_retrieved)

        # Check ports
        pod_ports_number = sum([len(c.ports) for c in k_pod_3.get_containers()])
        self.assertEqual(len(k_service.get_ports()), port_number + pod_ports_number)
        port_found = False

        port_list = []
        for c in k_pod_3.get_containers():
            for port in c.ports:
                port_list.append(port["containerPort"])

        for port in k_service.get_ports():
            if port.get("targetPort", port.get("port", 0)) in port_list:
                port_found = True
        self.assertTrue(port_found)
