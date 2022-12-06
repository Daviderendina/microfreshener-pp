from kubernetes.client import V1StatefulSetSpec
from kubernetes.client.models import V1StatefulSet

from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kMetadata import KMetadata
from project.kmodel.kPod import KPodTemplateSpec


class KStatefulSet(V1StatefulSet, KObject):

    @staticmethod
    def from_dict(description_dict):
        stateful_set = KStatefulSet()
        setattr(stateful_set, "api_version", description_dict.get("apiVersion", None))
        setattr(stateful_set, "kind", description_dict.get("kind", None))
        setattr(stateful_set, "metadata", KMetadata.from_dict(description_dict.get("metadata", None)))
        setattr(stateful_set, "spec", KStatefulSetSpec.from_dict(description_dict.get("spec", None)))

        stateful_set.set_attribute_order(description_dict)

        return stateful_set

    def get_pod_template_spec(self) -> KPodTemplateSpec:
        return self.spec.template

    def get_containers(self):
        return self.get_pod_template_spec().get_containers()

    def set_containers(self, container_list: list[KContainer]):
        self.get_pod_template_spec().spec.containers = container_list

    def get_labels(self):
        return self.get_pod_template_spec().get_labels()

    def is_host_network(self) -> bool:
        return True if self.get_pod_template_spec().spec.host_network else False

    def set_host_network(self, host_network: bool):
        self.get_pod_template_spec().spec.host_network = host_network


class KStatefulSetSpec(V1StatefulSetSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        selector_attribute = KStatefulSetSpec.attribute_map["selector"]
        service_name_attribute = KStatefulSetSpec.attribute_map["service_name"]
        template_attribute = KStatefulSetSpec.attribute_map["template"]

        spec = KStatefulSetSpec(
            selector=dictionary.get(selector_attribute, None),
            service_name=dictionary.get(service_name_attribute, None),
            template=KPodTemplateSpec.from_dict(dictionary.get(template_attribute, None))
        )

        spec.set_all_attributes_except(
            dictionary=dictionary,
            except_attributes=[selector_attribute, service_name_attribute, template_attribute]
        )

        spec.set_attribute_order(dictionary)

        return spec

