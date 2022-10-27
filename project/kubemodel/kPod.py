from kubernetes.client import V1PodSpec, V1PodTemplateSpec
from kubernetes.client.models import V1Pod

from project.kmodel.kObject import KObject
from project.kmodel.kMetadata import KMetadata
from project.kmodel.kContainer import KContainer


def parse_container_list(container_list: list):
    if container_list is None:
        return None

    result = list()
    for container in container_list:
        result.append(KContainer.from_dict(container))
    return result


class KPod(V1Pod, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        pod = KPod()
        pod.api_version = dictionary.get(pod.attribute_map["api_version"], None)
        pod.kind = dictionary.get(pod.attribute_map["kind"], None)
        pod.metadata = KMetadata.from_dict(dictionary.get(pod.attribute_map["metadata"], None))
        pod.spec = KPodSpec.from_dict(dictionary.get(pod.attribute_map["spec"], None))

        pod.set_attribute_order(dictionary)

        return pod

    def get_containers(self):
        return self.spec.containers

    def get_labels(self) -> dict[str, str]:
        return self.metadata.labels


class KPodSpec(V1PodSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        containers_attribute = KPodSpec.attribute_map["containers"]
        init_containers_attribute = KPodSpec.attribute_map["init_containers"]

        pod_spec = KPodSpec(
            containers=parse_container_list(dictionary.get(containers_attribute, None)),
            init_containers=parse_container_list(dictionary.get(init_containers_attribute, None))
        )

        pod_spec.set_all_attributes_except(
            dictionary=dictionary,
            except_attributes=[containers_attribute, init_containers_attribute]
        )

        pod_spec.set_attribute_order(dictionary)

        return pod_spec


class KPodTemplateSpec(V1PodTemplateSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        spec = KPodTemplateSpec(
            metadata=KMetadata.from_dict(dictionary.get(KPod.attribute_map["metadata"], None)),
            spec=KPodSpec.from_dict(dictionary.get(KPod.attribute_map["spec"], None)))

        spec.set_attribute_order(dictionary)

        return spec

    def get_labels(self) -> dict[str, str]:
        return self.metadata.labels

    def get_containers(self) -> list[KContainer]:
        return self.spec.containers


