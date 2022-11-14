from kubernetes.client import V1ServiceSpec, V1ServiceBackendPort
from kubernetes.client.models import V1Service

from project.kmodel.kObject import KObject
from project.kmodel.kMetadata import KMetadata


class KService(V1Service, KObject):

    @staticmethod
    def from_dict(dictionary):
        svc = KService()
        svc.api_version = dictionary.get(svc.attribute_map["api_version"], None)
        svc.kind = dictionary.get(svc.attribute_map["kind"], None)
        svc.metadata = KMetadata.from_dict(dictionary.get(svc.attribute_map["metadata"], None))
        svc.spec = KServiceSpec.from_dict(dictionary.get(svc.attribute_map["spec"], None))

        return svc

    def get_selectors(self) -> dict[str, str]:
        return self.spec.selector

    '''
    Return true if the service is accessible from outside the network
    '''
    def is_reachable_from_outside(self):
        return self.spec.type != "ClusterIP"

class KServiceSpec(V1ServiceSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        svc_spec = KServiceSpec()

        svc_spec.set_all_attributes_except(dictionary=dictionary)
        svc_spec.set_attribute_order(dictionary)
        return svc_spec


class KServiceBackendPort(V1ServiceBackendPort, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return dictionary

        ingress_svc = KServiceBackendPort()
        ingress_svc.name = dictionary.get(ingress_svc.attribute_map["name"], None)
        ingress_svc.number = dictionary.get(ingress_svc.attribute_map["number"], None)

        ingress_svc.set_attribute_order(dictionary)

        return ingress_svc
