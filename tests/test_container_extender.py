from unittest import TestCase

from microfreshener.core.model.microtosca import MicroToscaModel
from microfreshener.core.model.nodes import Service, MessageRouter, Compute
from microfreshener.core.model.relationships import DeployedOn

from project.extender.extender import KubeExtender
from project.extender.workerimpl.container_worker import ContainerWorker
from project.kmodel.kCluster import KCluster, KObjectKind
from project.kmodel.kDeployment import KDeployment
from project.kmodel.kPod import KPod
from project.kmodel.kReplicaSet import KReplicaSet
from project.kmodel.kService import KService
from project.kmodel.kStatefulSet import KStatefulSet

from data.kube_objects_dict import *


def _check_for_compute_added(model) -> (int, int):
    compute_found = 0
    relationship_found = 0
    for node in [c for c in list(model.nodes) if isinstance(c, Compute)]:
        compute_found += 1
        relationship_found += len([r for r in node.incoming_interactions if isinstance(r, DeployedOn)])
    return compute_found, relationship_found


class TestContainerExtender(TestCase):

    def test_no_pod(self):
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

    def test_pod_with_one_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        svc = KService.from_dict(DEFAULT_SVC)
        pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        cluster.add_object(svc, KObjectKind.SERVICE)
        cluster.add_object(pod, KObjectKind.POD)

        message_router_node = MessageRouter(name=svc.get_name_dot_namespace()+".svc.local.cluster")
        service_node = Service(name=pod.get_containers()[0].name + "." + pod.get_name_dot_namespace())
        model.add_node(message_router_node)
        model.add_node(service_node)
        model.add_interaction(message_router_node, service_node)

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 3)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 1)

    def test_pod_with_two_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        svc = KService.from_dict(DEFAULT_SVC)
        pod = KPod.from_dict(POD_WITH_TWO_CONTAINER)
        cluster.add_object(svc, KObjectKind.SERVICE)
        cluster.add_object(pod, KObjectKind.POD)

        mr_node = MessageRouter(name=svc.get_name_dot_namespace()+".svc")
        svc1_node = Service(name=pod.get_containers()[0].name + "." + pod.get_name_dot_namespace())
        svc2_node = Service(name=pod.get_containers()[1].name + "." + pod.get_name_dot_namespace())
        model.add_node(mr_node)
        model.add_node(svc1_node)
        model.add_node(svc2_node)
        model.add_interaction(mr_node, svc1_node)
        model.add_interaction(mr_node, svc2_node)

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 3)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 2)
        self.assertEqual(len(list(model.nodes)), 4)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 2)

    def test_deploy_with_one_container(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        deploy = KDeployment.from_dict(DEPLOYMENT_WITH_ONE_CONTAINER)
        cluster.add_object(deploy, KObjectKind.DEPLOYMENT)

        service_node = Service(name=deploy.get_pod_template_spec().get_containers()[0].name+"."+deploy.get_name_dot_namespace())
        model.add_node(service_node)

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

        svc1_node = Service(name=deploy.get_pod_template_spec().get_containers()[0].name+"."+deploy.get_name_dot_namespace())
        svc2_node = Service(name=deploy.get_pod_template_spec().get_containers()[1].name+"."+deploy.get_name_dot_namespace())
        model.add_node(svc1_node)
        model.add_node(svc2_node)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 2)
        self.assertFalse(Compute in list(map(type, model.nodes)))

        extender: KubeExtender = KubeExtender(worker_list=[ContainerWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects.items()), 1)
        self.assertEqual(len(list(model.nodes)), 3)

        compute_found, relationship_found = _check_for_compute_added(model=model)
        self.assertEqual(compute_found, 1)
        self.assertEqual(relationship_found, 2)

    def test_container_with_replicaset(self):
        model = MicroToscaModel(name="container-test-model")
        cluster = KCluster()

        rs = KReplicaSet.from_dict(REPLICASET_WITH_ONE_CONTAINER)
        cluster.add_object(rs, KObjectKind.REPLICASET)

        service_node = Service(name=rs.get_pod_template_spec().get_containers()[0].name+"."+rs.get_name_dot_namespace())
        model.add_node(service_node)

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

        template = statefulset.get_pod_template_spec()
        #TODO non funziona se il nome viene dato in automatico da K8s. Ad esempio utilizzando il campo generateName
        # oppure non mettendo il nome in un template, viene dato dopo il nome un codice del tipo "-ABCDD1234". Per
        # testare questa cosa, utilizzare la seguente istruzione per il nome:
        #name = template.get_containers()[0].name + "." + statefulset.metadata.name + "-ABCDD1234." + statefulset.get_namespace() \
        #    if not template.metadata.name \
        #    else template.get_containers()[0].name + "." + template.get_name_dot_namespace()

        name = template.get_containers()[0].name + "." + statefulset.metadata.name + "." + statefulset.get_namespace() \
            if not template.metadata.name \
            else template.get_containers()[0].name + "." + template.get_name_dot_namespace()
        model.add_node(Service(name=name))

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
