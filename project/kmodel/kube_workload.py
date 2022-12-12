from abc import abstractmethod
from typing import List

from project.kmodel.kube_container import KubeContainer
from project.kmodel.kube_object import KubeObject
from project.kmodel.utils import cast_container_list


def container_to_dict(container_list: list):
    return list(map(
        lambda c: c.data if isinstance(c, KubeContainer) else c,
        container_list
    ))


class KubeWorkload(KubeObject):

    def __init__(self, data: dict):
        super().__init__(data)

    @property
    @abstractmethod
    def containers(self) -> List[KubeContainer]:
        pass

    @abstractmethod
    def set_containers(self, container_list: []):
        pass

    @abstractmethod
    def get_labels(self):
        pass

    @abstractmethod
    def is_host_network(self) -> bool:
        pass

    @abstractmethod
    def set_host_network(self, host_network: bool):
        pass

    @abstractmethod
    def get_pod_spec(self):
        pass

    '''
    def get_container_ports(self):
        result = list()
        print("TODO: VEDERE COME FUNZIA")
        for container_port in self.containers:
            port = container_port.get("containerPort", None)
            if port is not None:
                result.append(port)
        return result
    '''


class KubePod(KubeWorkload):

    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def containers(self):
        return cast_container_list(self.data.get("spec", {}).get("containers", []))

    def set_containers(self, container_list):
        self.data["spec"]["containers"] = container_to_dict(container_list)

    def get_labels(self):
        return self.data.get("metadata", {}).get("labels", {})

    def is_host_network(self) -> bool:
        return self.data.get("spec", {}).get("hostNetwork", False)

    def set_host_network(self, host_network: bool):
        self.data["spec"]["hostNetwork"] = host_network

    def get_pod_spec(self):
        return self.data["spec"]


class KubePodDefiner(KubeWorkload):

    def __init__(self, data: dict):
        super().__init__(data)

    def get_pod_template(self):
        return self.data.get("spec", {}).get("template", {})

    @property
    def containers(self):
        return cast_container_list(self.get_pod_spec().get("containers", []))

    def set_containers(self, container_list):
        self.data["spec"]["template"]["spec"]["containers"] = container_to_dict(container_list)

    def get_labels(self):
        return self.get_pod_template().get("metadata", {}).get("labels", {})

    def is_host_network(self) -> bool:
        return self.get_pod_spec().get("hostNetwork", False)

    def set_host_network(self, host_network: bool):
        self.data["spec"]["template"]["spec"]["hostNetwork"] = host_network

    def get_pod_spec(self):
        return self.get_pod_template().get("spec", {})

    def add_pod_labels(self, labels: dict):
        actual_labels: dict = self.get_pod_template()["metadata"].get("labels", {})
        actual_labels.update(labels)
        self.get_pod_template()["metadata"]["labels"] = actual_labels


class KubeDeployment(KubePodDefiner):

    def __init__(self, data: dict):
        super().__init__(data)


class KubeReplicaSet(KubePodDefiner):

    def __init__(self, data: dict):
        super().__init__(data)


class KubeStatefulSet(KubePodDefiner):

    def __init__(self, data: dict):
        super().__init__(data)
