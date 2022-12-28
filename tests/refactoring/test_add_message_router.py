import copy
from unittest import TestCase

from microfreshener.core.analyser.smell import EndpointBasedServiceInteractionSmell
from microfreshener.core.model import Service, MicroToscaModel, MessageRouter

from k8s_template.kobject_generators import MF_NAME_SUFFIX
from tests.data.kube_objects_dict import POD_WITH_TWO_CONTAINER, POD_WITH_ONE_CONTAINER, DEFAULT_SVC, \
    DEPLOYMENT_WITH_ONE_CONTAINER
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.kmodel.kube_workload import KubePod, KubeDeployment

from project.solver.impl.add_message_router_refactoring import AddMessageRouterRefactoring


class TestRefactoringAddMessageRouter(TestCase):

    def test_add_service_with_pod_resource(self):
        model = MicroToscaModel("model")
        cluster = KubeCluster()

        # Create pods for cluster
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        k_pod_3 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))

        k_pod_1.data["metadata"]["name"] = "pod_1"
        k_pod_2.data["metadata"]["name"] = "pod_2"
        k_pod_3.data["metadata"]["name"] = "pod_3"

        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_pod_3)

        # Create TOSCA nodes
        node_svc_name_1 = k_pod_1.containers[0].name + "." + k_pod_1.typed_fullname
        node_svc_name_2 = k_pod_2.containers[0].name + "." + k_pod_2.typed_fullname
        node_svc_name_3 = k_pod_2.containers[1].name + "." + k_pod_2.typed_fullname
        node_svc_name_4 = k_pod_3.containers[0].name + "." + k_pod_3.typed_fullname

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
        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(cluster.services), 0)
        self.assertEqual(len([n for n in model.services]), 4)

        # Run solver
        solver: AddMessageRouterRefactoring = AddMessageRouterRefactoring(cluster, model)
        solver.apply(smell)

        # Check cluster
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(cluster.services), 1)

        # Check model
        self.assertEqual(len([n for n in model.services]), 4)
        self.assertEqual(len([n for n in model.message_routers]), 1)

        mr_node = list(model.message_routers)[0]
        self.assertTrue(len(mr_node.incoming_interactions), 3)
        self.assertTrue(len(mr_node.interactions), 1)
        self.assertEqual(mr_node.interactions[0].target, node_svc_4)
        sources = [node_svc_1, node_svc_2, node_svc_3]
        self.assertTrue(mr_node.incoming_interactions[0].source in sources)
        self.assertTrue(mr_node.incoming_interactions[1].source in sources)
        self.assertTrue(mr_node.incoming_interactions[2].source in sources)
        sources.remove(mr_node.incoming_interactions[0].source)
        sources.remove(mr_node.incoming_interactions[1].source)
        sources.remove(mr_node.incoming_interactions[2].source)
        self.assertEqual(len(sources), 0)

        # Get KubeService
        k_service = cluster.services[0]

        # Check name
        service_name = f"{k_pod_3.name}-{MF_NAME_SUFFIX}"
        service_ns = k_pod_3.namespace
        self.assertEqual(k_service.fullname, f"{service_name}.{service_ns}")

        # Check labels
        matching_labels = [l for l in k_service.selectors if l in k_pod_3.labels]
        self.assertEqual(len(matching_labels), 1)

        # Check ports
        # STRING_FORMAT: <NAME>_<PROTOCOL>_<PORT>_<TARGET_PORT>
        service_ports = []
        for sp in k_service.ports:
            self.assertTrue({sp['name']})
            matching_port = sp.get('target_port', None) if sp.get('target_port', None) else sp.get('port', None)
            service_ports.append(f"{sp.get('protocol', 'PROTOCOL')}  {matching_port}")

        for container in k_pod_3.containers:
            for port in container.ports:
                port_str = f"{port.get('protocol', 'PROTOCOL')}  {port.get('containerPort','PORT')}"
                self.assertTrue(port_str in service_ports)

    def test_add_service_with_deploy_resource(self):
        model = MicroToscaModel("model")
        cluster = KubeCluster()

        # Create pods for cluster
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        k_deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)

        k_pod_1.data["metadata"]["name"] = "pod_1"
        k_pod_2.data["metadata"]["name"] = "pod_2"

        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)
        cluster.add_object(k_deploy)

        # Create TOSCA nodes
        node_svc_name_1 = k_pod_1.containers[0].name + "." + k_pod_1.typed_fullname
        node_svc_name_2 = k_pod_2.containers[0].name + "." + k_pod_2.typed_fullname
        node_svc_name_3 = k_pod_2.containers[1].name + "." + k_pod_2.typed_fullname
        node_svc_name_4 = k_deploy.containers[0].name + "." + k_deploy.typed_fullname

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
        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(cluster.services), 0)

        # Run solver
        solver: AddMessageRouterRefactoring = AddMessageRouterRefactoring(cluster, model)
        solver.apply(smell)

        # Test solver output
        # Check cluster
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len(cluster.services), 1)
        k_service = cluster.services[0]

        # Check name
        service_name = f"{k_deploy.name}-{MF_NAME_SUFFIX}"
        service_ns = k_deploy.namespace
        self.assertEqual(k_service.fullname, f"{service_name}.{service_ns}")

        # Check labels
        matching_labels = [l for l in k_service.selectors if l in k_deploy.labels]
        self.assertEqual(len(matching_labels), 1)

        # Check ports
        # STRING_FORMAT: <NAME>_<PROTOCOL>_<PORT>_<TARGET_PORT>
        service_ports = []
        for sp in k_service.ports:
            self.assertTrue({sp['name']})
            matching_port = sp.get('target_port', None) if sp.get('target_port', None) else sp.get('port', None)
            service_ports.append(f"{sp.get('protocol', 'PROTOCOL')} {matching_port}")

        for container in k_deploy.containers:
            for port in container.ports:
                port_str = f"{port.get('protocol', 'PROTOCOL')} {port.get('containerPort', 'PORT')}"
                self.assertTrue(port_str in service_ports)

    #
    # def test_add_service_with_pod_resource_and_existing_service(self):
    #     model = MicroToscaModel("model")
    #     cluster = KubeCluster()
    #
    #     # Create objects for cluster
    #     labels = {'test': 'test_add_service_with_pod_resource_and_existing_service'}
    #
    #     k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
    #     k_pod_2 = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
    #     k_pod_3 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
    #     k_service = KubeService(copy.deepcopy(DEFAULT_SVC))
    #
    #     k_pod_1.data["metadata"]["name"] = "pod_1"
    #     k_pod_2.data["metadata"]["name"] = "pod_2"
    #     k_pod_3.data["metadata"]["name"] = "pod_3"
    #     k_pod_3.data["metadata"]["labels"] = labels
    #     k_service.data["spec"]["selector"] = labels
    #     k_service.data["spec"]["ports"] = [{'name': 'svc-port', 'port': 8081, 'protocol': 'TCP', 'targetPort': 8080}]
    #
    #     cluster.add_object(k_pod_1)
    #     cluster.add_object(k_pod_2)
    #     cluster.add_object(k_pod_3)
    #     cluster.add_object(k_service)
    #
    #     # Create TOSCA nodes
    #     node_svc_name_1 = k_pod_1.containers[0].name + "." + k_pod_1.typed_fullname
    #     node_svc_name_2 = k_pod_2.containers[0].name + "." + k_pod_2.typed_fullname
    #     node_svc_name_3 = k_pod_2.containers[1].name + "." + k_pod_2.typed_fullname
    #     node_svc_name_4 = k_pod_3.containers[0].name + "." + k_pod_3.typed_fullname
    #
    #     node_svc_1 = Service(node_svc_name_1)
    #     node_svc_2 = Service(node_svc_name_2)
    #     node_svc_3 = Service(node_svc_name_3)
    #     node_svc_4 = Service(node_svc_name_4)
    #     node_mr = MessageRouter(k_service.typed_fullname)
    #
    #     model.add_node(node_svc_1)
    #     model.add_node(node_svc_2)
    #     model.add_node(node_svc_3)
    #     model.add_node(node_svc_4)
    #     model.add_node(node_mr)
    #
    #     r1 = model.add_interaction(source_node=node_svc_1, target_node=node_svc_4)
    #     r2 = model.add_interaction(source_node=node_svc_2, target_node=node_mr)
    #     r3 = model.add_interaction(source_node=node_svc_3, target_node=node_mr)
    #     r4 = model.add_interaction(source_node=node_mr, target_node=node_svc_4)
    #
    #     smell = EndpointBasedServiceInteractionSmell(node=node_svc_4)
    #     smell.addLinkCause(r1)
    #
    #     port_number = len(k_service.ports)
    #
    #     # Assert that everything had been created properly
    #     self.assertEqual(len(cluster.cluster_objects), 4)
    #     self.assertEqual(len(cluster.services), 1)
    #     self.assertEqual(len([n for n in model.nodes]), 5)
    #     self.assertEqual(port_number, 1)
    #
    #     # Run solver
    #     solver: AddMessageRouterRefactoring = AddMessageRouterRefactoring(cluster, model)
    #     solver.apply(smell)
    #
    #     # Check cluster
    #     self.assertEqual(len(cluster.cluster_objects), 4)
    #     self.assertEqual(len(cluster.services), 1)
    #     self.assertEqual(len([n for n in model.nodes]), 5)
    #     k_service_retrieved = cluster.services[0]
    #     self.assertEqual(k_service, k_service_retrieved)
    #
    #     # Check model
    #     self.assertEqual(len([m for m in model.message_routers]), 1)
    #     mr_node = [m for m in model.message_routers][0]
    #     self.assertEqual(len([r for r in mr_node.incoming_interactions]), 3)
    #     self.assertEqual(len([r for r in mr_node.interactions]), 1)
    #     self.assertEqual(mr_node.interactions[0].target, node_svc_4)
    #
    #     targets = [node_svc_1, node_svc_2, node_svc_3]
    #     self.assertTrue(mr_node.incoming_interactions[0].source in targets)
    #     self.assertTrue(mr_node.incoming_interactions[1].source in targets)
    #     self.assertTrue(mr_node.incoming_interactions[2].source in targets)
    #     targets.remove(mr_node.incoming_interactions[0].source)
    #     targets.remove(mr_node.incoming_interactions[1].source)
    #     targets.remove(mr_node.incoming_interactions[2].source)
    #     self.assertEqual(len(targets), 0)
    #
    #     # Check ports
    #     pod_ports_number = sum([len(c.ports) for c in k_pod_3.containers])
    #     self.assertEqual(len(k_service.ports), port_number + pod_ports_number)
    #     port_found = False
    #
    #     port_list = []
    #     for c in k_pod_3.containers:
    #         for port in c.ports:
    #             port_list.append(port["containerPort"])
    #
    #     for port in k_service.ports:
    #         if port.get("targetPort", port.get("port", 0)) in port_list:
    #             port_found = True
    #     self.assertTrue(port_found)
    #
    # def test_add_service_with_deploy_resource_and_existing_service(self):
    #     model = MicroToscaModel("model")
    #     cluster = KubeCluster()
    #
    #     # Create objects for cluster
    #     labels = {'test': 'test_add_service_with_pod_resource_and_existing_service'}
    #
    #     k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
    #     k_pod_2 = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
    #     k_deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)
    #     k_service = KubeService(copy.deepcopy(DEFAULT_SVC))
    #
    #     k_pod_1.data["metadata"]["name"] = "pod_1"
    #     k_pod_2.data["metadata"]["name"] = "pod_2"
    #     k_deploy.pod_template["metadata"]["labels"] = labels
    #     k_service.data["spec"]["selector"] = labels
    #     k_service.data["spec"]["ports"] = [{'name': 'svc-port', 'port': 8081, 'protocol': 'TCP', 'targetPort': 8080}]
    #
    #     cluster.add_object(k_pod_1)
    #     cluster.add_object(k_pod_2)
    #     cluster.add_object(k_deploy)
    #     cluster.add_object(k_service)
    #
    #     # Create TOSCA nodes
    #     node_svc_name_1 = k_pod_1.containers[0].name + "." + k_pod_1.typed_fullname
    #     node_svc_name_2 = k_pod_2.containers[0].name + "." + k_pod_2.typed_fullname
    #     node_svc_name_3 = k_pod_2.containers[1].name + "." + k_pod_2.typed_fullname
    #     node_svc_name_4 = k_deploy.containers[0].name + "." + k_deploy.typed_fullname
    #
    #     node_svc_1 = Service(node_svc_name_1)
    #     node_svc_2 = Service(node_svc_name_2)
    #     node_svc_3 = Service(node_svc_name_3)
    #     node_svc_4 = Service(node_svc_name_4)
    #     node_mr = MessageRouter(k_service.typed_fullname)
    #
    #     model.add_node(node_svc_1)
    #     model.add_node(node_svc_2)
    #     model.add_node(node_svc_3)
    #     model.add_node(node_svc_4)
    #     model.add_node(node_mr)
    #
    #     r1 = model.add_interaction(source_node=node_svc_1, target_node=node_svc_4)
    #     r2 = model.add_interaction(source_node=node_svc_2, target_node=node_mr)
    #     r3 = model.add_interaction(source_node=node_svc_3, target_node=node_mr)
    #     r4 = model.add_interaction(source_node=node_mr, target_node=node_svc_4)
    #
    #     smell = EndpointBasedServiceInteractionSmell(node=node_svc_4)
    #     smell.addLinkCause(r1)
    #
    #     port_number = len(k_service.ports)
    #
    #     # Assert that everything had been created properly
    #     self.assertEqual(len(cluster.cluster_objects), 4)
    #     self.assertEqual(len(cluster.services), 1)
    #     self.assertEqual(len([n for n in model.nodes]), 5)
    #     self.assertEqual(port_number, 1)
    #
    #     # Run solver
    #     solver: AddMessageRouterRefactoring = AddMessageRouterRefactoring(cluster, model)
    #     solver.apply(smell)
    #
    #     # Test solver output
    #     # Check cluster
    #     self.assertEqual(len(cluster.cluster_objects), 4)
    #     self.assertEqual(len(cluster.services), 1)
    #     self.assertEqual(len([n for n in model.nodes]), 5)
    #     k_service_retrieved = cluster.services[0]
    #
    #     # Check name
    #     self.assertEqual(k_service, k_service_retrieved)
    #
    #     # Check ports
    #     pod_ports_number = sum([len(c.ports) for c in k_deploy.containers])
    #     self.assertEqual(len(k_service.ports), port_number + pod_ports_number)
    #     port_found = False
    #
    #     port_list = []
    #     for c in k_deploy.containers:
    #         for port in c.ports:
    #             port_list.append(port["containerPort"])
    #
    #     for port in k_service.ports:
    #         if port.get("targetPort", port.get("port", 0)) in port_list:
    #             port_found = True
    #     self.assertTrue(port_found)
