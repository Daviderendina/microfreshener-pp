import copy
from unittest import TestCase

from microfreshener.core.model.microtosca import MicroToscaModel
from microfreshener.core.model.nodes import Service, MessageRouter, Compute

from microkure.extender.extender import KubeExtender
from microkure.extender.worker_names import COMPUTE_NODE_WORKER
from microkure.kmodel.shortnames import KUBE_STATEFULSET

from tests.data.kube_objects_dict import *
from microkure.kmodel.kube_cluster import KubeCluster
from microkure.kmodel.kube_networking import KubeService
from microkure.kmodel.kube_workload import KubePod, KubeDeployment, KubeReplicaSet, KubeStatefulSet


def _check_for_compute_added(model) -> (int, int):
    compute_found = 0
    relationship_found = 0
    for node in [c for c in list(model.nodes) if isinstance(c, Compute)]:
        compute_found += 1
        relationship_found += len([r for r in node.deploys])
    return compute_found, relationship_found


class TestComputeNodeExtender(TestCase):

    def test_no_pod(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        svc: KubeService = KubeService(copy.deepcopy(DEFAULT_SVC))
        cluster.add_object(svc)

        model.add_node(Service(name=svc.name))

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)

    def test_pod_with_one_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        svc = KubeService(copy.deepcopy(DEFAULT_SVC))
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        cluster.add_object(svc)
        cluster.add_object(pod)

        message_router_node = MessageRouter(name=svc.typed_fullname)
        service_node = Service(name=pod.containers[0].name + "." + pod.typed_fullname)
        model.add_node(message_router_node)
        model.add_node(service_node)
        model.add_interaction(message_router_node, service_node)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 3)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_pod_with_two_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        svc = KubeService(copy.deepcopy(DEFAULT_SVC))
        pod = KubePod(copy.deepcopy(POD_WITH_TWO_CONTAINER))
        cluster.add_object(svc)
        cluster.add_object(pod)

        mr_node = MessageRouter(name=svc.typed_fullname)
        svc1_node = Service(name=pod.containers[0].name + "." + pod.typed_fullname)
        svc2_node = Service(name=pod.containers[1].name + "." + pod.typed_fullname)
        model.add_node(mr_node)
        model.add_node(svc1_node)
        model.add_node(svc2_node)
        model.add_interaction(mr_node, svc1_node)
        model.add_interaction(mr_node, svc2_node)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 2)
        self.assertEqual(len(list(model.nodes)), 4)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 2)

    def test_deploy_with_one_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        deploy = KubeDeployment(DEPLOYMENT_WITH_ONE_CONTAINER)
        cluster.add_object(deploy)

        service_node = Service(name=deploy.containers[0].name+"."+deploy.typed_fullname)
        model.add_node(service_node)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 2)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_container_with_deploy_two_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        deploy = KubeDeployment(DEPLOYMENT_WITH_TWO_CONTAINER)
        cluster.add_object(deploy)

        svc1_node = Service(name=deploy.containers[0].name+"."+deploy.typed_fullname)
        svc2_node = Service(name=deploy.containers[1].name+"."+deploy.typed_fullname)
        model.add_node(svc1_node)
        model.add_node(svc2_node)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 2)

    def test_container_with_replicaset(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        rs = KubeReplicaSet(REPLICASET_WITH_ONE_CONTAINER)
        cluster.add_object(rs)

        service_node = Service(name=rs.containers[0].name+"."+rs.typed_fullname)
        model.add_node(service_node)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 2)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_container_with_statefulset(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KubeCluster()

        statefulset = KubeStatefulSet(STATEFULSET_WITH_ONE_CONTAINER)
        cluster.add_object(statefulset)

        template = statefulset.pod_spec

        name = f"{statefulset.containers[0].name}.{statefulset.name}.{statefulset.namespace}.{KUBE_STATEFULSET}" \
            if not template.get("name", None) \
            else f"{statefulset.containers[0].name}.{template.fullname}.{KUBE_STATEFULSET}"
        model.add_node(Service(name=name))

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender([COMPUTE_NODE_WORKER])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 1)
        self.assertEqual(len(list(model.nodes)), 2)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)
