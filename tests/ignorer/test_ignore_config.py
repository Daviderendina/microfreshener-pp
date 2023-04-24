import copy
import os
from unittest import TestCase

from microfreshener.core.analyser.costants import REFACTORING_ADD_API_GATEWAY
from microfreshener.core.analyser.smell import NoApiGatewaySmell, WobblyServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter, Edge, Compute
from microfreshener.core.model.type import MICROTOSCA_NODES_SERVICE

from microkure.extender.extender import KubeExtender
from microkure.extender.worker_names import COMPUTE_NODE_WORKER, DATABASE_WORKER
from microkure.ignorer.impl.ignore_config import IgnoreConfig, IgnoreType
from microkure.ignorer.impl.manual_ignore_config import ManualIgnoreConfig
from microkure.kmodel.kube_cluster import KubeCluster
from microkure.kmodel.kube_workload import KubePod, KubeDeployment
from microkure.solver.solver import KubeSolver
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEPLOYMENT_WITH_ONE_CONTAINER


class TestIgnoreConfig(TestCase):

    # Tests with json
    def test_ignore_config(self):
        ignore_config = os.getcwd().split("tests")[0] + "/tests/data/ignore_config/ignore_config.json"
        ignore_config_schema = os.getcwd().split("tests")[0] + "/tests/../schema/ignore_config_schema.json"

        # Model
        model = MicroToscaModel("")
        svc = Service("container.name.namespace")
        mr = MessageRouter("name.namespace")
        model.add_node(svc)
        model.add_node(mr)

        # Ignore config
        ig = IgnoreConfig(ignore_config, ignore_config_schema)
        ig.import_config()

        # Check
        self.assertTrue(ig.is_ignored(svc, IgnoreType.WORKER, "Database"))
        self.assertFalse(ig.is_ignored(svc, IgnoreType.WORKER, "Compute-node"))

        self.assertFalse(ig.is_ignored(svc, IgnoreType.REFACTORING, "Use-timeout"))
        self.assertTrue(ig.is_ignored(mr, IgnoreType.REFACTORING, "Add-circuit-breaker"))

        self.assertTrue(ig.is_ignored(mr, IgnoreType.SMELLS, "all"))
        self.assertTrue(ig.is_ignored(mr, IgnoreType.SMELLS, "No-api-gateway"))

    def test_ignore_config_with_error(self):
        ignore_config = os.getcwd().split("tests")[0] + "/tests/data/ignore_config/ignore_config_error.json"
        ignore_config_schema = os.getcwd().split("tests")[0] + "/tests/../schema/ignore_config_schema.json"

        # Model
        model = MicroToscaModel("")
        svc = Service("container.name.namespace")
        mr = MessageRouter("name.namespace")
        model.add_node(svc)
        model.add_node(mr)

        try:
            # Ignore config
            ig = IgnoreConfig(ignore_config, ignore_config_schema)
            ig.import_config()

            self.assertIsNone(ig.config)
            self.assertIsNone(ig.schema)
        except ValueError:
            self.assertTrue(True)

    # Tests that refactor ignore works
    def test_ignore_all_refactor(self):
        # Code from test_add_api_gateway.test_pod_with_hostnetwork

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

        # Ignore config
        ignore_config = ManualIgnoreConfig()
        ignore_config.add_rule(svc.name, MICROTOSCA_NODES_SERVICE, IgnoreType.REFACTORING, "all")

        # Smell
        smell = NoApiGatewaySmell(svc)
        smell2 = WobblyServiceInteractionSmell(svc)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

        # Refactoring
        solver = KubeSolver(cluster, model, [REFACTORING_ADD_API_GATEWAY], ignore_config)
        solver.solve([smell, smell2])

        # Check that nothing changed
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

    def test_ignore_add_api_refactor(self):
        # Code from test_add_api_gateway.test_pod_with_hostnetwork

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

        # Ignore config
        ignore_config = ManualIgnoreConfig()
        ignore_config.add_rule(svc.name, MICROTOSCA_NODES_SERVICE, IgnoreType.REFACTORING, REFACTORING_ADD_API_GATEWAY)

        # Smell
        smell = NoApiGatewaySmell(svc)

        # Check model and cluster
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))

        # Refactoring
        solver = KubeSolver(cluster, model, [REFACTORING_ADD_API_GATEWAY], ignore_config)
        solver.solve([smell])

        # Check that nothing changed
        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len([n for n in model.nodes]), 1)
        self.assertEqual(len(model.edge.members), 1)
        self.assertTrue(isinstance(model.edge.members[0], Service))


    # Tests that worker ignore works

    def test_ignore_all_worker(self):

        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)
        deploy.containers[0].ports[0]["containerPort"] = 3306
        cluster.add_object(deploy)

        service_node = Service(name=deploy.containers[0].name+"."+deploy.typed_fullname)
        model.add_node(service_node)

        # Ignore config
        ignore_config = ManualIgnoreConfig()
        ignore_config.add_rule(service_node.name, MICROTOSCA_NODES_SERVICE, IgnoreType.WORKER, "all")

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.services)), 1)
        self.assertEqual(len(list(model.datastores)), 0)
        self.assertFalse(Compute in list(map(type, model.services)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER, DATABASE_WORKER])
        extender.extend(model, cluster, ignore_config)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.services)), 1)
        self.assertEqual(len(list(model.datastores)), 0)
        self.assertFalse(Compute in list(map(type, model.services)))

    def test_ignore_database_worker(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)
        deploy.containers[0].ports[0]["containerPort"] = 3306
        cluster.add_object(deploy)

        service_node = Service(name=deploy.containers[0].name+"."+deploy.typed_fullname)
        model.add_node(service_node)

        # Ignore config
        ignore_config = ManualIgnoreConfig()
        ignore_config.add_rule(service_node.name, MICROTOSCA_NODES_SERVICE, IgnoreType.WORKER, COMPUTE_NODE_WORKER)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.services)), 1)
        self.assertEqual(len(list(model.datastores)), 0)
        self.assertFalse(Compute in list(map(type, model.services)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER, DATABASE_WORKER])
        extender.extend(model, cluster, ignore_config)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.services)), 0)
        self.assertEqual(len(list(model.datastores)), 1)
        self.assertFalse(Compute in list(map(type, model.services)))



