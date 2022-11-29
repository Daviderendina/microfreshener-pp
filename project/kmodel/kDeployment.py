from kubernetes.client import V1DeploymentSpec
from kubernetes.client.models import V1Deployment

from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kMetadata import KMetadata
from project.kmodel.kPod import KPodTemplateSpec


class KDeployment(V1Deployment, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        deployment = KDeployment()

        deployment.api_version = dictionary.get(deployment.attribute_map["api_version"], None)
        deployment.kind = dictionary.get(deployment.attribute_map["kind"], None)
        deployment.metadata = KMetadata.from_dict(dictionary.get(deployment.attribute_map["metadata"], None))
        deployment.spec = KDeploymentSpec.from_dict(dictionary.get(deployment.attribute_map["spec"], None))

        deployment.set_attribute_order(dictionary)

        return deployment

    def get_pod_template_spec(self) -> KPodTemplateSpec:
        return self.spec.template

    def get_containers(self):
        return self.get_pod_template_spec().get_containers()

    def set_containers(self, container_list: list[KContainer]):
        self.get_pod_template_spec().spec.containers = container_list

    def get_labels(self):
        return self.get_pod_template_spec().get_labels()


class KDeploymentSpec(V1DeploymentSpec, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        selector_attribute=KDeploymentSpec.attribute_map["selector"]
        template_attribute=KDeploymentSpec.attribute_map["template"]
        replicas_attribute=KDeploymentSpec.attribute_map["replicas"]

        #TODO occhio ai template che forse è una lista

        spec = KDeploymentSpec(
            selector=dictionary.get(selector_attribute, ""),
            template=KPodTemplateSpec.from_dict(dictionary.get(template_attribute, None)),
            replicas=dictionary.get(replicas_attribute, None)
        )

        spec.set_all_attributes_except(dictionary, [selector_attribute, template_attribute, replicas_attribute])
        spec.set_attribute_order(dictionary)

        return spec
