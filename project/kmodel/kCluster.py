from project.kmodel.kDeployment import KDeployment
from project.kmodel.kIngress import KIngress
from project.kmodel.kObject import KObject
from enum import Enum

from project.kmodel.kPod import KPod, KPodTemplateSpec
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
    ISTIO_DESTINATION_RULE = "DestinationRule"

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
    DEFAULT_NAMESPACE = "default"

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
        sumlist = [v for k, v in objects]
        print(f" Objects: {sum(sumlist)} {dict(objects)}")

    def get_objects_by_kind(self, kind: KObjectKind):
        return self.cluster_objects.get(kind, [])

    def get_object_by_full_qualified_name(self, name_with_namespace: str) -> KObject:
        temp = []
        for obj in self.get_all_objects():
            if name_with_namespace == obj.get_name_dot_namespace():
                return obj

        return self._search_for_unnamed_match(name_with_namespace)

    def get_pod_template_spec_by_full_qualified_name(self, name_with_namespace: str) -> KPodTemplateSpec:
        for obj in self.get_all_objects():
            if isinstance(obj, KDeployment) or isinstance(obj, KStatefulSet) or isinstance(obj, KReplicaSet):
                if name_with_namespace == obj.get_pod_template_spec().get_name_dot_namespace():
                    return obj.spec.template

        return self._search_for_unnamed_match_pod_spec(name_with_namespace)

    def _search_for_unnamed_match(self, name: str) -> KObject:
        found_likely_objects = []
        for obj in self.get_all_objects():
            if not obj.metadata.name and obj.metadata.generate_name:
                if name.startswith(obj.metadata.generate_name) and name.endswith(obj.get_namespace()):
                    found_likely_objects.append(obj)

        if len(found_likely_objects) == 1:
            return found_likely_objects[0]

    def _search_for_unnamed_match_pod_spec(self, name: str) -> KPodTemplateSpec:
        found_likely_objects = []
        for obj in self.get_all_objects():
            if isinstance(obj, KDeployment) or isinstance(obj, KReplicaSet) or isinstance(obj, KStatefulSet):
                pod_template_spec = obj.get_pod_template_spec()

                if not pod_template_spec.metadata.name:
                    if name.startswith(obj.metadata.name) and name.endswith("."+pod_template_spec.get_namespace()):
                        found_likely_objects.append(pod_template_spec)

        if len(found_likely_objects) == 1:
            return found_likely_objects[0]

