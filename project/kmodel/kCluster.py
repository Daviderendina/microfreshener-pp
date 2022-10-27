from project.kmodel.kDeployment import KDeployment
from project.kmodel.kIngress import KIngress
from project.kmodel.kObject import KObject
from enum import Enum

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
    INGRESS = "Ingress"

    @staticmethod
    def get_members() -> list:
        return [KObjectKind.STATEFULSET]

    @staticmethod
    def get_from_class(class_type: type):
        type_kind_mapping: dict[class_type, KObjectKind] = {
            KPod: KObjectKind.POD,
            KDeployment: KObjectKind.DEPLOYMENT,
            KIngress: KObjectKind.INGRESS,
            KReplicaSet: KObjectKind.REPLICASET,
            KStatefulSet: KObjectKind.STATEFULSET,
            KService: KObjectKind.SERVICE
        }

        return type_kind_mapping.get(class_type, None)


class KCluster:

    def __init__(self):
        self.cluster_objects: dict[KObjectKind: list[KObject]] = dict()

    def add_object(self, obj: KObject, kind: KObjectKind):
        if kind not in self.cluster_objects.keys():
            self.cluster_objects[kind] = list()
        self.cluster_objects[kind].append(obj)

    def get_all_objects(self):
        result = list()
        for kType in self.cluster_objects.keys():
            for kObject in self.cluster_objects[kType]:
                result.append(kObject)
        return result

    def print_cluster(self):
        print("Cluster info:")
        objects = [(key.name, len(val)) for key, val in self.cluster_objects.items()]
        sumlist = [v for k,v in objects]
        print(f" Objects: {sum(sumlist)} {dict(objects)}")
