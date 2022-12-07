from enum import Enum

from typing import Dict

from project.kmodel.kDeployment import KDeployment
from project.kmodel.kIngress import KIngress
from project.kmodel.kPod import KPod
from project.kmodel.kReplicaSet import KReplicaSet
from project.kmodel.kService import KService
from project.kmodel.kStatefulSet import KStatefulSet


class KObjectKind(Enum):
    STATEFULSET = "StatefulSet",
    SERVICE = "Service",
    REPLICASET = "ReplicaSet",
    POD = "Pod",
    DEPLOYMENT = "Deployment",
    INGRESS = "Ingress",
    ISTIO_VIRTUAL_SERVICE = "VirtualService",
    ISTIO_DESTINATION_RULE = "DestinationRule",
    ISTIO_GATEWAY = "Gateway"

    @staticmethod
    def get_members() -> list:
        return [KObjectKind.STATEFULSET]

    @staticmethod
    def get_from_class(class_type: type):
        type_kind_mapping: Dict[class_type, KObjectKind] = {
            KPod: KObjectKind.POD,
            KDeployment: KObjectKind.DEPLOYMENT,
            KIngress: KObjectKind.INGRESS,
            KReplicaSet: KObjectKind.REPLICASET,
            KStatefulSet: KObjectKind.STATEFULSET,
            KService: KObjectKind.SERVICE
        }

        return type_kind_mapping.get(class_type, None)
