from abc import abstractmethod
from typing import List

from project.kmodel.kube_container import KubeContainer
from project.kmodel.kube_object import KubeObject
from project.kmodel.shortnames import KUBE_POD, KUBE_DEPLOYMENT, KUBE_REPLICASET, KUBE_STATEFULSET
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

    @property
    @abstractmethod
    def labels(self):
        pass

    @property
    @abstractmethod
    def host_network(self) -> bool:
        pass

    @abstractmethod
    def set_host_network(self, host_network: bool):
        pass

    @property
    @abstractmethod
    def pod_spec(self):
        pass


class KubePod(KubeWorkload):

    def __init__(self, data: dict):
        super().__init__(data)
        self.shortname = KUBE_POD

    @property
    def containers(self):
        return cast_container_list(self.data.get("spec", {}).get("containers", []), self)

    def set_containers(self, container_list):
        self.data["spec"]["containers"] = container_to_dict(container_list)

    @property
    def labels(self):
        return self.data.get("metadata", {}).get("labels", {})

    @property
    def host_network(self) -> bool:
        return self.data.get("spec", {}).get("hostNetwork", False)

    def set_host_network(self, host_network: bool):
        self.data["spec"]["hostNetwork"] = host_network

    @property
    def pod_spec(self):
        return self.data["spec"]


class KubePodDefiner(KubeWorkload):

    def __init__(self, data: dict):
        super().__init__(data)

    @property
    def pod_template(self):
        return self.data.get("spec", {}).get("template", {})

    @property
    def containers(self):
        return cast_container_list(self.pod_spec.get("containers", []), self)

    def set_containers(self, container_list):
        self.data["spec"]["template"]["spec"]["containers"] = container_to_dict(container_list)

    @property
    def labels(self):
        return self.pod_template.get("metadata", {}).get("labels", {})

    @property
    def host_network(self) -> bool:
        return self.pod_spec.get("hostNetwork", False)

    def set_host_network(self, host_network: bool):
        self.data["spec"]["template"]["spec"]["hostNetwork"] = host_network

    @property
    def pod_spec(self):
        return self.pod_template.get("spec", {})

    def add_pod_labels(self, labels: dict):
        actual_labels: dict = self.pod_template["metadata"].get("labels", {})
        actual_labels.update(labels)
        self.pod_template["metadata"]["labels"] = actual_labels


class KubeDeployment(KubePodDefiner):

    def __init__(self, data: dict):
        super().__init__(data)
        self.shortname = KUBE_DEPLOYMENT


class KubeReplicaSet(KubePodDefiner):

    def __init__(self, data: dict):
        super().__init__(data)
        self.shortname = KUBE_REPLICASET


class KubeStatefulSet(KubePodDefiner):

    def __init__(self, data: dict):
        super().__init__(data)
        self.shortname = KUBE_STATEFULSET
