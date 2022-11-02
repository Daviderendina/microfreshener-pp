from unittest import TestCase

from microfreshener.core.model.microtosca import MicroToscaModel
from microfreshener.core.model.nodes import Service, MessageRouter

from project.extender.extender import KubeExtender
from project.extender.kubeworker import ContainerWorker, Compute
from project.importer.yamlkimporter import YamlKImporter
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kDeployment import KDeployment
from project.kmodel.kPod import KPod
from project.kmodel.kReplicaSet import KReplicaSet
from project.kmodel.kService import KService
from project.kmodel.kStatefulSet import KStatefulSet

from tests.kube_objects_dict import *


def _check_for_compute_added(model) -> (int, int):
    compute_found = 0
    relationship_found = 0
    for node in list(model.nodes):
        if isinstance(node, Service):
            for link in node.interactions:
                target = link.target
                if isinstance(target, Compute):
                    compute_found += 1
                    relationship_found += 1

    return compute_found, relationship_found


class TestKubeExtender(TestCase):

    # TODO manca tesstare le relazioni pure

    def test_get_dict(self):
        pass

        importer = YamlKImporter().Import(
            "/home/davide/PycharmProjects/microfreshener-update(OLD)/data/yaml_files/test")
        for k, v in importer.cluster_objects.items():
            print(v[0])


    def test_container_no_pod(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        svc = KService.from_dict(DEFAULT_SVC)
        cluster.add_object(svc, KObjectKind.SERVICE)

        model.add_node(Service(name=svc.metadata.name))

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)

    def test_container_with_pod_one_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        svc = KService.from_dict(DEFAULT_SVC)
        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        cluster.add_object(svc, KObjectKind.SERVICE)
        cluster.add_object(pod, KObjectKind.POD)

        model.add_node(MessageRouter(name=svc.metadata.name))
        model.add_node(Service(name=pod.metadata.name))

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 3)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_container_with_pod_two_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        svc = KService.from_dict(DEFAULT_SVC)
        pod = KPod.from_dict(POD_WITH_TWO_CONTAINER)
        cluster.add_object(svc, KObjectKind.SERVICE)
        cluster.add_object(pod, KObjectKind.POD)

        model.add_node(MessageRouter(name=svc.metadata.name))
        model.add_node(Service(name=pod.metadata.name))

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 4)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 2)
        self.assertEqual(relationship_found, 2)

    def test_container_with_deploy_one_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        deploy = KDeployment.from_dict(DEPLOYMENT_WITH_ONE_CONTAINER)
        cluster.add_object(deploy, KObjectKind.DEPLOYMENT)

        model.add_node(Service(name=deploy.spec.template.metadata.name))  # TODO siamo sicuri?

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 2)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_container_with_deploy_two_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        deploy = KDeployment.from_dict(DEPLOYMENT_WITH_TWO_CONTAINER)
        cluster.add_object(deploy, KObjectKind.DEPLOYMENT)

        model.add_node(Service(name=deploy.spec.template.metadata.name))  # TODO siamo sicuri?

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 2)
        self.assertEqual(relationship_found, 2)

    def test_container_with_replicaset(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        rs = KReplicaSet.from_dict(REPLICASET_WITH_ONE_CONTAINER)
        cluster.add_object(rs, KObjectKind.REPLICASET)

        model.add_node(Service(name=rs.spec.template.metadata.name))  # TODO siamo sicuri?

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 2)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_container_with_statefulset(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        statefulset = KStatefulSet.from_dict(STATEFULSET_WITH_ONE_CONTAINER)
        cluster.add_object(statefulset, KObjectKind.STATEFULSET)

        model.add_node(Service(name=statefulset.spec.template.metadata.name))  # TODO siamo sicuri?

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 1)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 2)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)
