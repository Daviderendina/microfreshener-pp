from kubernetes.client import V1ContainerPort
from kubernetes.client.models import V1Container

from project.kmodel.kObject import KObject


class KContainer(V1Container, KObject):

    @staticmethod
    def from_dict(dictionary):
        if dictionary is None:
            return None

        name_attribute = KContainer.attribute_map["name"]

        container = KContainer(name=dictionary.get(name_attribute, None))

        container.set_all_attributes_except(
            dictionary=dictionary,
            except_attributes=[name_attribute]
        )
        container.set_attribute_order(dictionary)

        return container

    def get_container_ports(self) -> list[int]:
        result = list()
        for container_port in self.ports:
            port = container_port.get("containerPort", None)
            if port is not None:
                result.append(port)
        return result
