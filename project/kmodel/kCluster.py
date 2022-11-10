from project.kmodel.kContainer import KContainer
from project.kmodel.kDeployment import KDeployment
from project.kmodel.kObject import KObject

from project.kmodel.kPod import KPod, KPodTemplateSpec
from project.kmodel.kReplicaSet import KReplicaSet
from project.kmodel.kService import KService
from project.kmodel.kStatefulSet import KStatefulSet
from project.kmodel.kobject_kind import KObjectKind


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

    def get_objects_by_kind(self, *args) -> list[KObject]:
        result = []
        for arg in args:
            result += self.cluster_objects.get(arg, [])
        return result

    def get_container_by_tosca_model_name(self, service_name: str) -> KContainer:
        for pod in self.get_objects_by_kind(KObjectKind.POD):
            for container in pod.get_containers():
                tosca_name = container.name + "." + pod.get_name_dot_namespace()
                if tosca_name == service_name:
                    return container

        for template in self.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.STATEFULSET, KObjectKind.REPLICASET):
            for container in template.get_pod_template_spec().get_containers():
                tosca_name = container.name + template.get_name_dot_namespace()
                if tosca_name == service_name:
                    return container

    def find_pods_exposed_by_service(self, service: KService) -> list[KPod]:
        exposed_pods = []
        for pod in self.get_objects_by_kind(KObjectKind.POD):
            if pod.get_labels():
                service_selectors = [k+":"+v for k,v in service.get_selectors().items()]
                pod_labels = [k+":"+v for k,v in pod.get_labels().items()]
                if len([value for value in pod_labels if value in service_selectors]) > 0:
                    exposed_pods.append(pod)
        return exposed_pods

    def find_pods_defining_object_exposed_by_service(self, service: KService) -> list[KObject]:
        exposed_pods = []
        for template_defining_obj in self.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.REPLICASET, KObjectKind.STATEFULSET):
            service_selectors = [k + ":" + v for k, v in service.get_selectors().items()]
            pod_labels = [k + ":" + v for k, v in template_defining_obj.get_labels().items()]
            if len([value for value in pod_labels if value in service_selectors]) > 0:
                exposed_pods.append(template_defining_obj)

        return exposed_pods
