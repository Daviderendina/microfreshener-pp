from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Edge, MessageRouter

from project.extender.extender import KubeExtender
from project.extender.workerimpl.ingress_worker import IngressWorker
from project.kmodel.kCluster import KCluster
from data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC, DEFAULT_SVC_INGRESS
from project.kmodel.kIngress import KIngress

from project.kmodel.kPod import KPod
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


class TestIngressExtender(TestCase):

    '''
    Case:
    Ingress controller: not present in the model
    Kube Service: NodePort (reachable from outside)
    Edge Group: Contains ClusterIP Service
    '''
    def test_expose_nodeport_in_edge(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge(name="edge"))
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_svc.spec.type = "NodePort"
        k_pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod.metadata.labels = {'app': 'test'}
        k_ingress = KIngress.from_dict(DEFAULT_SVC_INGRESS)
        k_ingress.spec.rules[0].http.paths[0].backend.service.name = k_svc.metadata.name
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod, KObjectKind.POD)
        cluster.add_object(k_ingress, KObjectKind.INGRESS)

        # Add Service to Tosca Model
        svc = Service(k_pod.get_containers()[0].name + "." + k_pod.get_fullname())
        mr = MessageRouter(k_svc.get_fullname() + ".svc.cluster.local")
        model.add_node(svc)
        model.add_node(mr)
        model.edge.add_member(mr)
        model.add_interaction(source_node=mr, target_node=svc)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len([n for n in model.nodes]), 3)

        ic_node: MessageRouter = [n for n in model.nodes if n.name == IngressWorker.INGRESS_CONTROLLER_DEFAULT_NAME][0]

        self.assertTrue(ic_node in model.edge)
        self.assertTrue(mr in model.edge)
        self.assertTrue(svc not in model.edge)

        self.assertEqual(len(ic_node.interactions), 1)
        self.assertEqual(len(ic_node.incoming_interactions), 0)
        self.assertEqual(len(mr.interactions), 1)
        self.assertEqual(len(mr.incoming_interactions), 1)
        self.assertEqual(len(svc.interactions), 0)
        self.assertEqual(len(svc.incoming_interactions), 1)

    '''
    Case: 
    Ingress controller: present in the model, no interaction
    Kube Service: ClusterIP (not reachable from outside)
    Edge Group: Contains ClusterIP Service, Ingress Controller
    '''
    def test_expone_clusterip_in_edge(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge(name="edge"))
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_svc.spec.type = "ClusterIP"
        k_pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod.metadata.labels = {'app': 'test'}
        k_ingress = KIngress.from_dict(DEFAULT_SVC_INGRESS)
        k_ingress.spec.rules[0].http.paths[0].backend.service.name = k_svc.metadata.name
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod, KObjectKind.POD)
        cluster.add_object(k_ingress, KObjectKind.INGRESS)

        # Add Service to Tosca Model
        svc = Service(k_pod.get_containers()[0].name + "." + k_pod.get_fullname())
        mr = MessageRouter(k_svc.get_fullname() + ".svc.cluster.local")
        ic_name = "nginx-ingress-controller-32ede32-fer34"
        ic = MessageRouter(ic_name)
        model.add_node(svc)
        model.add_node(mr)
        model.add_node(ic)
        model.edge.add_member(mr)
        model.edge.add_member(ic)
        model.add_interaction(source_node=mr, target_node=svc)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 3)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len([n for n in model.nodes]), 3)

        ic_node: MessageRouter = [n for n in model.nodes if n.name == ic_name][0]

        self.assertTrue(ic_node in model.edge)
        self.assertTrue(mr not in model.edge)
        self.assertTrue(svc not in model.edge)

        self.assertEqual(len(ic_node.interactions), 1)
        self.assertEqual(len(ic_node.incoming_interactions), 0)
        self.assertEqual(len(mr.interactions), 1)
        self.assertEqual(len(mr.incoming_interactions), 1)
        self.assertEqual(len(svc.interactions), 0)
        self.assertEqual(len(svc.incoming_interactions), 1)


    '''
    Case: 
    Ingress controller: present in the model, no interaction
    Kube Service: ClusterIP (not reachable from outside)
    Edge Group: Contains ClusterIP Service, Ingress Controller
    '''
    def test_expone_clusterip_not_in_edge(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge(name="edge"))
        cluster = KCluster()

        # Add objects to cluster
        k_svc = KService.from_dict(DEFAULT_SVC)
        k_svc.spec.type = "ClusterIP"
        k_pod = KPod.from_dict(POD_WITH_ONE_CONTAINER)
        k_pod.metadata.labels = {'app': 'test'}
        k_ingress = KIngress.from_dict(DEFAULT_SVC_INGRESS)
        k_ingress.spec.rules[0].http.paths[0].backend.service.name = k_svc.metadata.name
        cluster.add_object(k_svc, KObjectKind.SERVICE)
        cluster.add_object(k_pod, KObjectKind.POD)
        cluster.add_object(k_ingress, KObjectKind.INGRESS)

        # Add Service to Tosca Model
        svc = Service(k_pod.get_containers()[0].name + "." + k_pod.get_fullname())
        mr = MessageRouter(k_svc.get_fullname() + ".svc.cluster.local")
        ic_name = "nginx-ingress-controller-32ede32-fer34"
        ic = MessageRouter(ic_name)
        model.add_node(svc)
        model.add_node(mr)
        model.add_node(ic)
        model.edge.add_member(ic)
        model.add_interaction(source_node=mr, target_node=svc)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len(list(model.nodes)), 3)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.get_all_objects()), 3)
        self.assertEqual(len([n for n in model.nodes]), 3)

        ic_node: MessageRouter = [n for n in model.nodes if n.name == ic_name][0]

        self.assertTrue(ic_node in model.edge)
        self.assertTrue(mr not in model.edge)
        self.assertTrue(svc not in model.edge)

        self.assertEqual(len(ic_node.interactions), 1)
        self.assertEqual(len(ic_node.incoming_interactions), 0)
        self.assertEqual(len(mr.interactions), 1)
        self.assertEqual(len(mr.incoming_interactions), 1)
        self.assertEqual(len(svc.interactions), 0)
        self.assertEqual(len(svc.incoming_interactions), 1)
    