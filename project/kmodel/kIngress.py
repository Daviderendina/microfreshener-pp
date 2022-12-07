from kubernetes.client import V1IngressSpec, V1IngressBackend, V1HTTPIngressPath, V1HTTPIngressRuleValue, \
    V1IngressRule, V1IngressServiceBackend
from kubernetes.client.models import V1Ingress
from typing import List

from project.kmodel.kObject import KObject, parse_list
from project.kmodel.kMetadata import KMetadata
from project.kmodel.kService import KServiceBackendPort


class KIngress(V1Ingress, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return

        ingress = KIngress()

        ingress.api_version = dictionary.get(ingress.attribute_map["api_version"], None)
        ingress.kind = dictionary.get(ingress.attribute_map["kind"], None)
        ingress.metadata = KMetadata.from_dict(dictionary.get(ingress.attribute_map["metadata"], None))
        ingress.spec = KIngressSpec.from_dict(dictionary.get(ingress.attribute_map["spec"], None))

        ingress.set_attribute_order(dictionary)

        return ingress

    def get_exposed_svc_names(self) -> List[str]:
        result: List[str] = list()

        rules = self.spec.rules
        for rule in rules:
            paths = rule.http.paths
            for path in paths:
                result.append(path.backend.service.name)

        return result


class KIngressSpec(V1IngressSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        ingress_spec = KIngressSpec()

        ingress_spec.default_backend = dictionary.get(ingress_spec.attribute_map["default_backend"], None)
        ingress_spec.ingress_class_name = dictionary.get(ingress_spec.attribute_map["ingress_class_name"], None)
        ingress_spec.rules = parse_list(KIngressRule, dictionary.get(ingress_spec.attribute_map["rules"], None))
        ingress_spec.tls = dictionary.get(ingress_spec.attribute_map["tls"], None)

        ingress_spec.set_attribute_order(dictionary)

        return ingress_spec


class KIngressBackend(V1IngressBackend, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return dictionary

        ingress_backend = KIngressBackend()

        ingress_backend.resource = dictionary.get(KIngressBackend.attribute_map["resource"], None)
        ingress_backend.service = KIngressServiceBackend.from_dict(
            dictionary.get(ingress_backend.attribute_map["service"], None))

        ingress_backend.set_attribute_order(dictionary)

        return ingress_backend


class KHttpIngressPath(V1HTTPIngressPath, KObject):

    @staticmethod
    def from_dict(dictionary):
        ingress_path = KHttpIngressPath(
            path=dictionary.get(KHttpIngressPath.attribute_map["path"], None),
            path_type=dictionary.get(KHttpIngressPath.attribute_map["path_type"], None),
            backend=KIngressBackend.from_dict(
                dictionary.get(KHttpIngressPath.attribute_map["backend"], None))
        )

        ingress_path.set_attribute_order(dictionary)

        return ingress_path


class KHttpIngressRuleValue(V1HTTPIngressRuleValue, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        rule_value = KHttpIngressRuleValue(
            paths=parse_list(
                destination_class=KHttpIngressPath,
                dictionary_list=dictionary.get(KHttpIngressRuleValue.attribute_map["paths"], None))
        )

        rule_value.set_attribute_order(dictionary)

        return rule_value


class KIngressRule(V1IngressRule, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        ingress_rule = KIngressRule()

        ingress_rule.host = dictionary.get(KIngressRule.attribute_map["host"], None)
        ingress_rule.http = KHttpIngressRuleValue.from_dict(dictionary.get(KIngressRule.attribute_map["http"], None))

        ingress_rule.set_attribute_order(dictionary)

        return ingress_rule


class KIngressServiceBackend(V1IngressServiceBackend, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        ingress_service = KIngressServiceBackend(
            name=dictionary.get(KIngressServiceBackend.attribute_map["name"], None),
            port=KServiceBackendPort.from_dict(dictionary.get(KIngressServiceBackend.attribute_map["port"], None))
        )

        ingress_service.set_attribute_order(dictionary)

        return ingress_service
