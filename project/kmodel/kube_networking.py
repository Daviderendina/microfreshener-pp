from project.kmodel.kube_object import KubeObject
from project.kmodel.kube_utils import does_selectors_labels_match, name_has_namespace, does_svc_match_ports
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

    @property
    def type(self):
        return self.data.get("spec", {}).get("type", "ClusterIP")

    '''
    Return true if the service is accessible from outside the network
    '''
    def is_reachable_from_outside(self):
        return self.type != "ClusterIP"

    def does_expose_workload(self, workload: KubeWorkload):
        return does_selectors_labels_match(self.selectors, workload.labels) and \
               self._does_match_ports([item for sublist in [c.ports for c in workload.containers] for item in sublist])

    def can_expose_workload(self, workload: KubeWorkload, only_ports: list = None):
        label_match = does_selectors_labels_match(self.selectors, workload.labels)
        ports_to_consider = only_ports if only_ports else workload.all_defined_ports

        return label_match and not self._does_match_ports(ports_to_consider)

    def _does_match_ports(self, ports_to_check):
        for svc_port in self.ports:
            for w_port in ports_to_check:
                # If targetPort is not defined, port is considered
                port_to_consider = svc_port.get("targetPort", svc_port.get("port", None))
                target_port_match = \
                    port_to_consider == w_port.get("name", "") or \
                    port_to_consider == w_port.get("containerPort", "")

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

        return [s if name_has_namespace(s) else f"{s}.{self.namespace}" for s in result]
