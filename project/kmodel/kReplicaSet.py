from kubernetes.client import V1ReplicaSetSpec
from kubernetes.client.models import V1ReplicaSet

from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kMetadata import KMetadata
from project.kmodel.kPod import KPodTemplateSpec


class KReplicaSet(V1ReplicaSet, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        replicaset = KReplicaSet()

        replicaset.api_version = dictionary.get(replicaset.attribute_map["api_version"], None)
        replicaset.kind = dictionary.get(replicaset.attribute_map["kind"], None)
        replicaset.metadata = KMetadata.from_dict(dictionary.get(replicaset.attribute_map["metadata"], None))
        replicaset.spec = KReplicaSetSpec.from_dict(dictionary.get(replicaset.attribute_map["spec"], None))

        replicaset.set_attribute_order(dictionary)

        return replicaset

    def get_pod_spec(self) -> KPodTemplateSpec:
        return self.spec.template

    def get_pod_template_spec(self) -> KPodTemplateSpec:
        return self.spec.template

    def get_containers(self):
        return self.get_pod_template_spec().get_containers()

    def set_containers(self, container_list: list[KContainer]):
        self.get_pod_template_spec().spec.containers = container_list

    def get_labels(self):
        return self.get_pod_template_spec().get_labels()

    def is_host_network(self) -> bool:
        return self.get_pod_template_spec().spec.host_network

class KReplicaSetSpec(V1ReplicaSetSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        selector_attribute = KReplicaSetSpec.attribute_map["selector"]
        template_attribute = KReplicaSetSpec.attribute_map["template"]

        spec = KReplicaSetSpec(
            selector=dictionary.get(selector_attribute, None),
            template=KPodTemplateSpec.from_dict(dictionary.get(template_attribute, None))
        )

        spec.set_all_attributes_except(
            dictionary=dictionary,
            except_attributes=[template_attribute, selector_attribute]
        )

        spec.set_attribute_order(dictionary)

        return spec
