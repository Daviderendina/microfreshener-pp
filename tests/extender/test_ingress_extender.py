import copy
from unittest import TestCase

from microfreshener.core.model import MicroToscaModel, Service, Edge, MessageRouter, KIngress

from project.extender.extender import KubeExtender
from project.extender.impl.ingress_worker import IngressWorker
from tests.data.kube_objects_dict import POD_WITH_ONE_CONTAINER, DEFAULT_SVC, DEFAULT_SVC_INGRESS
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService, KubeIngress
from project.kmodel.kube_workload import KubePod


def _get_ingress_rule_dict(path, name, port):
    return {
        "http": {
            "paths": [
                {
                    "path": path,
                    "pathType": "Prefix",
                    "backend": {
                        "service": {
                            "name": name,
                            "port": {
                                "number": port
                            }
                        }
                    }
                }
            ]
        }
    }


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
        cluster = KubeCluster()

        # Add objects to cluster
        k_svc = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_svc.data["spec"]["type"] = "NodePort"
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod.data["metadata"]["labels"] = {'app': 'test'}
        k_ingress = KubeIngress(DEFAULT_SVC_INGRESS)
        k_ingress.data["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"] = k_svc.name
        cluster.add_object(k_svc)
        cluster.add_object(k_pod)
        cluster.add_object(k_ingress)

        # Add Service to Tosca Model
        svc = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        mr = MessageRouter(k_svc.typed_fullname)
        model.add_node(svc)
        model.add_node(mr)
        model.edge.add_member(mr)
        model.add_interaction(source_node=mr, target_node=svc)

        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(list(model.nodes)), 2)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len([n for n in model.nodes]), 3)

        ic_node: MessageRouter = [n for n in model.message_routers if n.name == k_ingress.typed_fullname][0]

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
        cluster = KubeCluster()

        # Add objects to cluster
        k_svc = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_svc.data["spec"]["type"] = "ClusterIP"
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod.data["metadata"]["labels"] = {'app': 'test'}
        k_ingress = KubeIngress(DEFAULT_SVC_INGRESS)
        k_ingress.data["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"] = k_svc.name
        cluster.add_object(k_svc)
        cluster.add_object(k_pod)
        cluster.add_object(k_ingress)

        # Add Service to Tosca Model
        svc = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        mr = MessageRouter(k_svc.typed_fullname)
        ic_name = "nginx-ingress-controller-32ede32-fer34.ing"
        ic = MessageRouter(ic_name)
        model.add_node(svc)
        model.add_node(mr)
        model.add_node(ic)
        model.edge.add_member(mr)
        model.edge.add_member(ic)
        model.add_interaction(source_node=mr, target_node=svc)

        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(list(model.nodes)), 3)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len([n for n in model.nodes]), 4)

        ic_node: MessageRouter = [n for n in model.nodes if n.name == k_ingress.typed_fullname][0]

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

    def test_expose_clusterip_not_in_edge(self):
        model = MicroToscaModel(name="service-model")
        model.add_group(Edge(name="edge"))
        cluster = KubeCluster()

        # Add objects to cluster
        k_svc = KubeService(copy.deepcopy(DEFAULT_SVC))
        k_svc.data["spec"]["type"] = "ClusterIP"
        k_pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        k_pod.data["metadata"]["labels"] = {'app': 'test'}
        k_ingress = KubeIngress(DEFAULT_SVC_INGRESS)
        k_ingress.data["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"] = k_svc.name
        cluster.add_object(k_svc)
        cluster.add_object(k_pod)
        cluster.add_object(k_ingress)

        # Add Service to Tosca Model
        svc = Service(k_pod.containers[0].name + "." + k_pod.typed_fullname)
        mr = MessageRouter(k_svc.typed_fullname)
        ic_name = "nginx-ingress-controller-32ede32-fer34.ing"
        ic = MessageRouter(ic_name)
        model.add_node(svc)
        model.add_node(mr)
        model.add_node(ic)
        model.edge.add_member(ic)
        model.add_interaction(source_node=mr, target_node=svc)

        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len(list(model.nodes)), 3)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        self.assertEqual(len(cluster.cluster_objects), 3)
        self.assertEqual(len([n for n in model.nodes]), 4)

        ic_node: MessageRouter = [n for n in model.nodes if n.name == k_ingress.typed_fullname][0]

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
    Ingress controller: present in the model with 2 interactions (total interaction is 4)
    Kube Service: 4 present in the cluster but only 2 with interaction with the Ingress (one defined with another rule 
        and the other defined with one more path)
    '''
    def test_add_missing_service_interaction(self):
        model = MicroToscaModel(name="test_add_missing_service_interaction")
        model.add_group(Edge(name="edge"))
        cluster = KubeCluster()

        # Cluster
        svc_1 = KubeService(copy.deepcopy(DEFAULT_SVC))
        svc_2 = KubeService(copy.deepcopy(DEFAULT_SVC))
        svc_3 = KubeService(copy.deepcopy(DEFAULT_SVC))
        svc_4 = KubeService(copy.deepcopy(DEFAULT_SVC))

        svc_1.data["metadata"]["name"] = f"{svc_1.data['metadata']['name']}_1"
        svc_2.data["metadata"]["name"] = f"{svc_2.data['metadata']['name']}_2"
        svc_3.data["metadata"]["name"] = f"{svc_3.data['metadata']['name']}_3"
        svc_4.data["metadata"]["name"] = f"{svc_4.data['metadata']['name']}_4"

        ingress = KubeIngress(DEFAULT_SVC_INGRESS)
        double_path = _get_ingress_rule_dict("/path3", svc_3.fullname, svc_3.ports[0]["port"])
        double_path["http"]["paths"].append({
                    "path": "/path4",
                    "pathType": "Prefix",
                    "backend": {
                        "service": {
                            "name": svc_4.fullname,
                            "port": {
                                "number": svc_4.ports[0]["port"]
                            }
                        }
                    }
                })

        ingress.data["spec"]["rules"] = [
            _get_ingress_rule_dict("/path1", svc_1.fullname, svc_1.ports[0]["port"]),
            _get_ingress_rule_dict("/path2", svc_2.fullname, svc_2.ports[0]["port"]),
            double_path
        ]

        cluster.add_object(svc_1)
        cluster.add_object(svc_2)
        cluster.add_object(svc_3)
        cluster.add_object(svc_4)
        cluster.add_object(ingress)

        # Model
        mr_1 = MessageRouter(svc_1.typed_fullname)
        mr_2 = MessageRouter(svc_2.typed_fullname)
        mr_3 = MessageRouter(svc_3.typed_fullname)
        mr_4 = MessageRouter(svc_4.typed_fullname)
        ing = MessageRouter(ingress.typed_fullname)

        model.add_node(mr_1)
        model.add_node(mr_2)
        model.add_node(mr_3)
        model.add_node(mr_4)
        model.add_node(ing)
        model.edge.add_member(ing)

        model.add_interaction(ing, mr_1)
        model.add_interaction(ing, mr_2)

        # Check model
        self.assertEqual(len(cluster.cluster_objects), 5)
        self.assertEqual(len(list(model.nodes)), 5)

        self.assertEqual(len(mr_1.interactions), 0)
        self.assertEqual(len(mr_1.incoming_interactions), 1)
        self.assertEqual(len(mr_2.interactions), 0)
        self.assertEqual(len(mr_2.incoming_interactions), 1)
        self.assertEqual(len(mr_3.interactions), 0)
        self.assertEqual(len(mr_3.incoming_interactions), 0)
        self.assertEqual(len(mr_4.interactions), 0)
        self.assertEqual(len(mr_4.incoming_interactions), 0)
        self.assertEqual(len(ing.interactions), 2)
        self.assertEqual(len(ing.incoming_interactions), 0)

        extender: KubeExtender = KubeExtender(worker_list=[IngressWorker()])
        extender.extend(model, cluster)

        # Check
        self.assertEqual(len(cluster.cluster_objects), 5)
        self.assertEqual(len(list(model.nodes)), 5)

        self.assertEqual(len(mr_1.interactions), 0)
        self.assertEqual(len(mr_1.incoming_interactions), 1)
        self.assertEqual(len(mr_2.interactions), 0)
        self.assertEqual(len(mr_2.incoming_interactions), 1)
        self.assertEqual(len(mr_3.interactions), 0)
        self.assertEqual(len(mr_3.incoming_interactions), 1)
        self.assertEqual(len(mr_4.interactions), 0)
        self.assertEqual(len(mr_4.incoming_interactions), 1)
        self.assertEqual(len(ing.interactions), 4)
        self.assertEqual(len(ing.incoming_interactions), 0)

        self.assertEqual(mr_3.incoming_interactions[0].source, ing)
        self.assertEqual(mr_4.incoming_interactions[0].source, ing)




