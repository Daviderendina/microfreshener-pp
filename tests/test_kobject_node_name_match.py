import copy
from unittest import TestCase

from microfreshener.core.model import Service

from project.kmodel.kube_workload import KubePod
from project.kmodel.shortnames import KUBE_POD
from project.utils.utils import check_kobject_node_name_match
from data.kube_objects_dict import POD_WITH_ONE_CONTAINER


class TestKObjectNodeNameMatch(TestCase):

    # Case: node.name = name.namespace.pod
    def test_name_ns(self):
        pod_name = "name"
        pod_ns = "namespace"

        # Create pod
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod_name
        pod.data["metadata"]["namespace"] = pod_ns

        # Create node
        node = Service(f"{pod_name}.{pod_ns}.{KUBE_POD}")

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

    # Case: node.name = container.name.namespace.pod
    def test_container_name_ns(self):
        pod_name = "name"
        pod_ns = "namespace"

        # Create pod
        pod = KubePod(copy.deepcopy(POD_WITH_ONE_CONTAINER))
        pod.data["metadata"]["name"] = pod_name
        pod.data["metadata"]["namespace"] = pod_ns

        # Create node
        node = Service(name=f"{pod.containers[0].name}.{pod_name}.{pod_ns}.{KUBE_POD}")

        # Check function
        self.assertTrue(check_kobject_node_name_match(pod.containers[0], node))


