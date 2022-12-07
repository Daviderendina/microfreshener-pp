import re

from typing import List

from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kPod import KPod
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind


class KCluster:
    DEFAULT_NAMESPACE = "default"

    def __init__(self):
        self.cluster_objects: dict[KObjectKind: List[KObject]] = dict()

    def add_object(self, obj: KObject, kind: KObjectKind):
        if kind not in self.cluster_objects.keys():
            self.cluster_objects[kind] = list()
        self.cluster_objects[kind].append(obj)

    def remove_object(self, obj: KObject):
        kind = KObjectKind.get_from_class(obj.__class__)
        if kind in self.cluster_objects.keys():
            self.cluster_objects[kind].remove(obj)


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

    def get_objects_by_kind(self, *args) -> List[KObject]:
        result = []
        for arg in args:
            result += self.cluster_objects.get(arg, [])
        return result

    def get_container_by_tosca_model_name(self, service_name: str) -> KContainer:
        container_list = []
        for obj in self.get_objects_by_kind(KObjectKind.POD, KObjectKind.DEPLOYMENT, KObjectKind.STATEFULSET, KObjectKind.REPLICASET):
            container_list += [(obj.get_fullname(), c) for c in obj.get_containers()]

        for object_fullname, container in container_list:
            tosca_name = container.name + "." + object_fullname
            if tosca_name == service_name:
                return container

    def find_pods_exposed_by_service(self, service: KService) -> List[KPod]:
        exposed_pods = []
        for pod in self.get_objects_by_kind(KObjectKind.POD):
            if pod.get_labels():
                service_selectors = [k+":"+v for k,v in service.get_selectors().items()]
                pod_labels = [k+":"+v for k,v in pod.get_labels().items()]
                if len([value for value in pod_labels if value in service_selectors]) > 0:
                    exposed_pods.append(pod)
        return exposed_pods

    def find_defining_obj_exposed_by_service(self, service: KService) -> List[KObject]:
        exposed_pods = []
        for defining_obj in self.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.REPLICASET, KObjectKind.STATEFULSET):
            service_selectors = [k + ":" + v for k, v in service.get_selectors().items()]
            pod_labels = [k + ":" + v for k, v in defining_obj.get_labels().items()]
            if len([value for value in pod_labels if value in service_selectors]) > 0:
                exposed_pods.append(defining_obj)

        return exposed_pods

    def get_object_by_name(self, name: str, kind: KObjectKind = None) -> KObject:
        object_list = self.get_objects_by_kind(kind) if kind else self.get_all_objects()

        for obj in object_list:

            # Case: name is FQDN
            result = re.match(obj.get_fullname() + r"[.][a-zA-Z]*[.]cluster[.]local", name)
            if result and result.string == name:
                return obj

            # Case: name is <name>.<namespace>
            if obj.get_fullname() == name:
                return obj

            # Case: name is only <name>
            possible = []
            if obj.metadata.name == name:
                possible.append(obj)
            if len(possible) == 1:
                return possible[0]

    def find_services_which_expose_object(self, object: KObject) -> List[KService]:
        #TODO mi invento qualcosa di meglio che questo if?
        if isinstance(object, KPod):
            object_labels = object.get_labels()
        else:
            object_labels = object.get_pod_template_spec().get_labels()

        exposing_svc = []

        for svc in self.get_objects_by_kind(KObjectKind.SERVICE):
            matching_labels = [l for l in object_labels.items() if l in svc.get_selectors().items()]
            if len(matching_labels) > 0:
                exposing_svc.append(svc)

        return exposing_svc

    def get_container_defining_object(self, container: KContainer):
        for pod in self.get_objects_by_kind(KObjectKind.POD):
            for pod_container in pod.get_containers():
                if pod_container == container:
                    return pod

        def_list = self.get_objects_by_kind(KObjectKind.DEPLOYMENT, KObjectKind.REPLICASET, KObjectKind.STATEFULSET)
        for defining_obj in def_list:
            for obj_container in defining_obj.get_containers():
                if obj_container == container:
                    return defining_obj

        return None
