import copy
from unittest import TestCase

from microfreshener.core.analyser.smell import NoApiGatewaySmell
from microfreshener.core.model import MicroToscaModel, Edge, Service, MessageRouter

from k8s_template.kobject_generators import MF_NODEPORT_SERVICE_SUFFIX
from project.report.report import RefactoringReport
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEPLOYMENT_WITH_ONE_CONTAINER, POD_WITH_TWO_CONTAINER
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_workload import KubePod, KubeDeployment

from project.solver.impl.add_API_gateway_refactoring import AddAPIGatewayRefactoring


def apply_solver(solver, smell):
    pending_ops = []
    solver.set_solver_pending_ops(pending_ops)
    solver.apply(smell)
    for ops, obj in pending_ops:
        ops(obj)


class TestAddAPIGatewayRefactoring(TestCase):

    service_suffix = MF_NODEPORT_SERVICE_SUFFIX

    '''
    Test case: Pod has hostNetwork set as True. Contains also deeper tests on MessageRouter created
    '''
    def test_pod_with_hostnetwork(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod.data["spec"]["hostNetwork"] = True
        cluster.add_object(k_pod)

        # Model
        svc = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        model.add_node(svc)
        model.edge.add_member(svc)

        # Smell
        smell = NoApiGatewaySmell(svc)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        apply_solver(solver, smell)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))

        k_services: list = cluster.services
        self.assertEquals(len(k_services), 1)
        k_service = k_services[0]

        self.assertFalse(k_pod.data["spec"]["hostNetwork"])

        self.assertEqual(k_service.fullname, f"{k_pod.name}-{self.service_suffix}.{k_pod.namespace}")
        self.assertTrue(f"{k_pod.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")

        # Check ports
        self.assertEqual(len(k_service.ports), len(k_pod.containers[0].ports))
        self.assertEqual(len(k_service.ports), 2)
        self.assertEqual(k_service.ports[0]["node_port"], 30000)
        self.assertEqual(k_service.ports[1]["node_port"], 30001)

        # Check message router
        self.assertEqual(model.edge.members[0].name, k_service.typed_fullname)
        self.assertEqual(list(model.message_routers)[0].interactions[0].target, svc)
        self.assertEqual(len(list(model.message_routers)[0].interactions), 1)


    '''
    Test case: one port has hostPort set and the other not
    '''
    def test_pod_with_host_port(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        pod_host_port = 90
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod.containers[0].ports[0]["hostPort"] = pod_host_port
        cluster.add_object(k_pod)

        # Model
        svc = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        model.add_node(svc)
        model.edge.add_member(svc)

        # Smell
        smell = NoApiGatewaySmell(svc)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        solver.apply(smell)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))

        k_services: list = cluster.services
        self.assertEquals(len(k_services), 1)
        k_service = k_services[0]

        self.assertEqual(len(k_service.ports), 1)

        self.assertEqual(k_service.fullname, f"{k_pod.name}-{self.service_suffix}.{k_pod.namespace}")
        self.assertTrue(f"{k_pod.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")

        for container in k_pod.containers:
            for port in container.ports:
                self.assertIsNone(port.get("hostPort"))

        self.assertEqual(len(k_service.ports), 1)

        container_name = k_pod.containers[0].name
        k_pod_port_strings = [
            f"{container_name}.{p.get('name', k_pod.fullname+'-port-'+str(p['containerPort'])+'-mf')} {p.get('protocol', 'PROTOCOL?')} {p['containerPort']}"
            for p in k_pod.containers[0].ports[0:0]] # I take only the 0 cause is the one with hostPort set
        k_svc_port_strings = [
            f"{p.get('name', '')} {p.get('protocol', 'PROTOCOL?')} {p['port']}" for p in k_service.ports]
        for port in k_pod_port_strings:
            self.assertTrue(port in k_svc_port_strings)

        # Check node port
        self.assertEqual(k_service.ports[0]["node_port"], 30000)

    '''
    Test case: Deployment has hostNetwork set as True
    '''
    def test_deployment_with_hostnetwork(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        k_deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)
        k_deploy.pod_spec["hostNetwork"] = True
        cluster.add_object(k_deploy)

        # Model
        svc = Service(k_deploy.containers[0].name + "." + k_deploy.typed_fullname)
        model.add_node(svc)
        model.edge.add_member(svc)

        # Smell
        smell = NoApiGatewaySmell(svc)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        apply_solver(solver, smell)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))

        self.assertFalse(k_deploy.pod_spec["hostNetwork"])

        k_services: list = cluster.services
        self.assertEquals(len(k_services), 1)
        k_service = k_services[0]

        self.assertEqual(k_service.fullname, f"{k_deploy.name}-{self.service_suffix}.{k_deploy.namespace}")
        self.assertTrue(f"{k_deploy.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")

        # Check ports
        self.assertEqual(len(k_service.ports), len(k_deploy.containers[0].ports))
        self.assertEqual(len(k_service.ports), 1)
        self.assertEqual(k_service.ports[0]["node_port"], 30000)


    '''
    Test case: one port has hostPort set and the other not
    '''
    def test_deployment_with_host_port(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        deployment_host_port = 90
        k_deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)
        k_deploy.containers[0].ports[0]["hostPort"] = deployment_host_port
        cluster.add_object(k_deploy)


        # Model
        svc = Service(k_deploy.containers[0].name + "." + k_deploy.typed_fullname)
        model.add_node(svc)
        model.edge.add_member(svc)

        # Smell
        smell = NoApiGatewaySmell(svc)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        solver.apply(smell)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))

        k_services: list = cluster.services
        self.assertEquals(len(k_services), 1)
        k_service = k_services[0]

        self.assertEqual(len(k_service.ports), 1)

        self.assertEqual(k_service.fullname, f"{k_deploy.name}-{self.service_suffix}.{k_deploy.namespace}")
        self.assertTrue(f"{k_deploy.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")

        # Check hostPort is none
        for container in k_deploy.containers:
            for port in container.ports:
                self.assertIsNone(port.get("hostPort"))

        # Check ports
        k_pod_port_strings = [
            f"{p.get('name', k_deploy.fullname+'-port-'+str(p['containerPort'])+'-mf')} {p.get('protocol', 'PROTOCOL?')} {p['containerPort']}"
            for p in k_deploy.containers[0].ports]
        k_svc_port_strings = [
            f"{p.get('name', '')} {p.get('protocol', 'PROTOCOL?')} {p['port']}"
            for p in k_service.ports]

        self.assertEqual(len(k_service.ports), 1)
        self.assertEqual(len(k_pod_port_strings), 1)
        for port in k_pod_port_strings:
            self.assertTrue(port in k_svc_port_strings)

        # Check service exponed ports
        self.assertEqual(k_service.ports[0]["node_port"], 30000)

    '''
    Test case: the pod defines two container and has hostNetwork = True
    '''
    def test_pod_with_two_container_host_port(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        host_ports = [80, 81]
        k_pod = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        k_pod.containers[1].ports[0]['containerPort'] = 8001
        k_pod.containers[0].ports[0]['hostPort'] = host_ports[0]
        k_pod.containers[1].ports[0]['hostPort'] = host_ports[1]
        cluster.add_object(k_pod)

        # Model
        svc_1 = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        svc_2 = Service(k_pod.containers[1].name + "." + k_pod.typed_fullname)
        model.add_node(svc_1)
        model.add_node(svc_2)
        model.edge.add_member(svc_1)
        model.edge.add_member(svc_2)

        # Smell
        smell_1 = NoApiGatewaySmell(svc_1)
        smell_2 = NoApiGatewaySmell(svc_2)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 2)
        self.assertTrue(isinstance(model.edge.members[0], Service))
        self.assertTrue(isinstance(model.edge.members[1], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        solver.apply(smell_1)
        solver.apply(smell_2)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 3)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))

        k_services: list = cluster.services
        self.assertEquals(len(k_services), 1)
        k_service = k_services[0]

        self.assertEqual(k_service.fullname, f"{k_pod.name}-{self.service_suffix}.{k_pod.namespace}")
        self.assertTrue(f"{k_pod.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")

        # Check that hostPort is removed
        for container in k_pod.containers:
            for port in container.ports:
                self.assertIsNone(port.get("hostPort"))

        self.assertEqual(len(k_service.ports), 2)
        self.assertEqual(k_service.ports[0]["node_port"], 30000)
        self.assertEqual(k_service.ports[1]["node_port"], 30001)

        self.assertEqual(list(model.message_routers)[0].interactions[0].target, svc_1)
        self.assertEqual(list(model.message_routers)[0].interactions[1].target, svc_2)
        self.assertEqual(len(list(model.message_routers)[0].interactions), 2)

    '''
    Test case: two pod are defined with hostNetwork = True, but expose the same port. 
    '''
    def test_pod_with_two_container_hostnetwork_equal_ports(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        k_pod_1 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_2 = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod_1.data["metadata"]["name"] = k_pod_1.data["metadata"]["name"] + "_1"
        k_pod_2.data["metadata"]["name"] = k_pod_2.data["metadata"]["name"] + "_2"
        k_pod_1.data["spec"]["hostNetwork"] = True
        k_pod_2.data["spec"]["hostNetwork"] = True
        k_pod_1.containers[0].ports[0]['containerPort'] = 8000
        k_pod_2.containers[0].ports[0]['containerPort'] = 8000
        del k_pod_1.containers[0].ports[1]
        del k_pod_2.containers[0].ports[1]
        labels = {"test_pod_with_two_container_hostnetwork_equal_ports": "svc"}
        k_pod_1.data["metadata"]["labels"] = labels
        k_pod_2.data["metadata"]["labels"] = labels
        cluster.add_object(k_pod_1)
        cluster.add_object(k_pod_2)


            # # Cluster
            # k_pod = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
            # k_pod.data["spec"]["hostNetwork"] = True
            # k_pod.containers[0].ports[0]['containerPort'] = 8000
            # k_pod.containers[1].ports[0]['containerPort'] = 8000
            # cluster.add_object(k_pod)

        # Model
        svc_1 = Service(k_pod_1.containers[0].name + "." + k_pod_1.typed_fullname)
        svc_2 = Service(k_pod_2.containers[0].name + "." + k_pod_2.typed_fullname)
        model.add_node(svc_1)
        model.add_node(svc_2)
        model.edge.add_member(svc_1)
        model.edge.add_member(svc_2)

        # Smell
        smell_1 = NoApiGatewaySmell(svc_1)
        smell_2 = NoApiGatewaySmell(svc_2)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 2)
        self.assertTrue(isinstance(model.edge.members[0], Service))
        self.assertTrue(isinstance(model.edge.members[1], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        pending_ops = []
        solver.set_solver_pending_ops(pending_ops)
        solver.apply(smell_1)
        solver.apply(smell_2)
        for ops, obj in pending_ops:
            ops(obj)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 4)
        self.assertEqual(len([n for n in model.nodes]), 4)
        self.assertEqual(len(model.edge.members), 2)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))
        self.assertTrue(isinstance(model.edge.members[1], MessageRouter))

        k_services: list = cluster.services
        self.assertEqual(len(k_services), 2)

        # Test service 1
        k_service = k_services[0]

        self.assertEqual(k_service.fullname, f"{k_pod_1.name}-{self.service_suffix}.{k_pod_1.namespace}")
        self.assertTrue(f"{k_pod_1.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")
        self.assertFalse(k_pod_1.data["spec"]["hostNetwork"])

        all_pod_ports_strings = [
            f"{p.get('name', k_pod_1.containers[0].name+'.'+k_pod_1.fullname+'-port-'+str(p['containerPort'])+'-mf')} {p.get('protocol', 'PROTOCOL?')} {p['containerPort']} {p['containerPort']}"
            for p in k_pod_1.containers[0].ports]
        all_pod_ports_strings += [
            f"{p.get('name', k_pod_2.containers[0].name + '.' + k_pod_2.fullname + '-port-' + str(p['containerPort']) + '-mf')} {p.get('protocol', 'PROTOCOL?')} {p['containerPort']} {p['containerPort']}"
            for p in k_pod_2.containers[0].ports]

        k_svc_port_strings = [
            f"{p.get('name', '')} {p.get('protocol', 'PROTOCOL?')} {p['port']} {p['node_port']}"
            for p in k_service.ports]
        self.assertEqual(len(k_service.ports), 1)
        self.assertEqual(k_service.ports[0]["node_port"], 30000)

        # Test service 2
        k_service = k_services[1]

        self.assertEqual(k_service.fullname, f"{k_pod_2.name}-{self.service_suffix}.{k_pod_2.namespace}")
        self.assertTrue(f"{k_pod_2.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")
        self.assertFalse(k_pod_2.data["spec"]["hostNetwork"])

        self.assertEqual(len(k_service.ports), 1)
        self.assertEqual(k_service.ports[0]["node_port"], 30000)

        # Model check
        self.assertEqual(len(list(model.message_routers)[0].interactions), 1)
        self.assertEqual(len(list(model.message_routers)[0].interactions), 1)
        self.assertEqual(list(model.message_routers)[0].interactions[0].target, svc_1)
        self.assertEqual(list(model.message_routers)[1].interactions[0].target, svc_2)

    '''
    Test case: the pod defines two container and has hostNetwork = True
    '''
    def test_pod_with_two_container_hostnetwork(self):
        model = MicroToscaModel("model")
        model.add_group(Edge("edge"))
        cluster = KubeCluster()

        # Cluster
        k_pod = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        k_pod.data["spec"]["hostNetwork"] = True
        k_pod.containers[0].ports[0]['containerPort'] = 8001
        k_pod.containers[1].ports[0]['containerPort'] = 8000
        cluster.add_object(k_pod)

        # Model
        svc_1 = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        svc_2 = Service(k_pod.containers[1].name + "." + k_pod.typed_fullname)
        model.add_node(svc_1)
        model.add_node(svc_2)
        model.edge.add_member(svc_1)
        model.edge.add_member(svc_2)

        # Smell
        smell_1 = NoApiGatewaySmell(svc_1)
        smell_2 = NoApiGatewaySmell(svc_2)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 2)
        self.assertEqual(len(model.edge.members), 2)
        self.assertTrue(isinstance(model.edge.members[0], Service))
        self.assertTrue(isinstance(model.edge.members[1], Service))

        # Refactoring
        solver: AddAPIGatewayRefactoring = AddAPIGatewayRefactoring(cluster, model)
        solver.apply(smell_1)
        apply_solver(solver, smell_2)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len([n for n in model.nodes]), 3)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], MessageRouter))

        k_services: list = cluster.services
        self.assertEquals(len(k_services), 1)
        k_service = k_services[0]

        self.assertFalse(k_pod.data["spec"]["hostNetwork"])

        self.assertEqual(k_service.fullname, f"{k_pod.name}-{self.service_suffix}.{k_pod.namespace}")
        self.assertTrue(f"{k_pod.fullname}-svc-mf" in k_service.selectors.keys())
        self.assertEqual(k_service.data["spec"]["type"], "NodePort")

        # Check ports
        self.assertEqual(len(k_service.ports), len(k_pod.containers[0].ports + k_pod.containers[1].ports))
        self.assertEqual(len(k_service.ports), 2)
        self.assertEqual(k_service.ports[0]["node_port"], 30000)
        self.assertEqual(k_service.ports[1]["node_port"], 30001)

        RefactoringReport().export()
