from project.kmodel.kube_object import KubeObject
from project.kmodel.kube_utils import does_selectors_labels_match
from project.kmodel.kube_workload import KubeWorkload
from project.kmodel.shortnames import KUBE_INGRESS, KUBE_SERVICE


class KubeNetworking(KubeObject):
    pass


class KubeService(KubeNetworking):

    def __init__(self, data: dict):
        super().__init__(data)
        self.shortname = KUBE_SERVICE

    @property
    def selectors(self):
        return self.data.get("spec", {}).get("selector", {})

    @property
    def ports(self):
        return self.data.get("spec", {}).get("ports", [])

    '''
    Return true if the service is accessible from outside the network
    '''
    def is_reachable_from_outside(self):
        return self.data.get("spec", {}).get("type", "ClusterIP") != "ClusterIP"

    def does_expose_workload(self, workload: KubeWorkload):
        if not does_selectors_labels_match(self.selectors, workload.labels):
            return False

        workload_ports = [item for sublist in [c.ports for c in workload.containers] for item in sublist]
        for svc_port in self.ports:
            for w_port in workload_ports:
                target_port_match = \
                    svc_port.get("targetPort", None) == w_port.get("name", "") or \
                    svc_port.get("targetPort", None) == w_port.get("containerPort", "")
                protocol_match = svc_port.get("protocol", "TCP") == w_port.get("protocol", "TCP")

                if target_port_match and protocol_match:
                    return True

        return False


class KubeIngress(KubeNetworking):

    def __init__(self, data: dict):
        super().__init__(data)
        self.shortname = KUBE_INGRESS

    def get_exposed_svc_names(self):
        result = list()

        rules = self.data.get("spec", {}).get("rules", [])
        for rule in rules:
            paths = rule.get("http", {}).get("paths", [])
            for path in paths:
                svc_name = path.get("backend", {}).get("service", {}).get("name", None)
                if svc_name:
                    result.append(svc_name)

        return result
