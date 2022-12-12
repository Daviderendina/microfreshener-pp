import copy
from unittest import TestCase

from microfreshener.core.model import Service

from project.kmodel.kube_workload import KubePod
from project.utils import check_kobject_node_name_match
from data.kube_objects_dict import POD_WITH_ONE_CONTAINER


class TestKObjectNodeNameMatch(TestCase):

    # Case: node.name = name.namespace
    def test_name_ns(self):
        pod_name = "name"
        pod_ns = "namespace"

        # Create pod
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod_name
        pod.data["metadata"]["namespace"] = pod_ns

        # Create node
        node = Service(name=pod_name+"."+pod_ns)

        # Check function
        self.assertTrue(check_kobject_node_name_match(pod, node))

    # Case: node.name = name.namespace.svc.cluster.local
    def test_name_ns_with_hostname(self):
        pod_name = "name"
        pod_ns = "namespace"

        # Create pod
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod_name
        pod.data["metadata"]["namespace"] = pod_ns

        # Create node
        node = Service(name=pod_name+"."+pod_ns+".svc.cluster.local")

        # Check function
        self.assertTrue(check_kobject_node_name_match(pod, node))

    # Case: node.name = name
    def test_name(self):
        pod_name = "name"
        pod_ns = "namespace"

        # Create pod
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod_name
        pod.data["metadata"]["namespace"] = pod_ns

        # Create node
        node = Service(name=pod_name)

        # Check function
        self.assertFalse(check_kobject_node_name_match(pod, node))

    # Case: node.name = container.name.namespace
    def test_container_name_ns(self):
        pod_name = "name"
        pod_ns = "namespace"

        # Create pod
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod_name
        pod.data["metadata"]["namespace"] = pod_ns

        # Create node
        node = Service(name=f"{pod.get_containers()[0].name}.{pod_name}.{pod_ns}")

        # Check function
        self.assertFalse(check_kobject_node_name_match(pod.get_containers()[0], node))
        self.assertTrue(check_kobject_node_name_match(pod.get_containers()[0], node, defining_obj_fullname=pod.fullname))


