import re
from typing import List

from project.exporter.export_object import ExportObject
from project.kmodel.kube_istio import KubeVirtualService, KubeDestinationRule, KubeIstioGateway
from project.kmodel.kube_networking import KubeService, KubeIngress, KubeNetworking
from project.kmodel.kube_object import KubeObject
from project.kmodel.kube_workload import KubeWorkload


class KubeCluster:

    def __init__(self):
        self.cluster_objects: list[KubeObject] = list()
        self.cluster_export_info: list[ExportObject] = list()

    @property
    def workloads(self):
        return [obj for obj in self.cluster_objects if isinstance(obj, KubeWorkload)]

    @property
    def networkings(self):
        return [n for n in self.cluster_objects if isinstance(n, KubeNetworking)]

    @property
    def services(self):
        return [svc for svc in self.cluster_objects if isinstance(svc, KubeService)]

    @property
    def containers(self):
        #TODO tornare direttamente l'oggetto!!!
        return [(w.typed_fullname, w.containers) for w in self.workloads] #TODO typed?

    @property
    def ingress(self):
        return [ing for ing in self.cluster_objects if isinstance(ing, KubeIngress)]

    @property
    def virtual_services(self):
        return [vs for vs in self.cluster_objects if isinstance(vs, KubeVirtualService)]

    @property
    def destination_rules(self):
        return [dr for dr in self.cluster_objects if isinstance(dr, KubeDestinationRule)]

    @property
    def istio_gateways(self):
        return [ig for ig in self.cluster_objects if isinstance(ig, KubeIstioGateway)]

    def add_object(self, kube_object):
        if not kube_object in self.cluster_objects:
            self.cluster_objects.append(kube_object)

    def remove_object(self, kube_object):
        if kube_object in self.cluster_objects:
            self.cluster_objects.remove(kube_object)

    def add_export_object(self, export_object: ExportObject):
        self.cluster_export_info.append(export_object)

    def find_workload_exposed_by_svc(self, service: KubeService) -> List[KubeWorkload]:
        exposed_obj = []
        for workload in self.workloads:
            service_selectors = [f"{k}:{v}" for k, v in service.selectors.items()]
            pod_labels = [f"{k}:{v}" for k, v in workload.labels.items()]
            if len([value for value in pod_labels if value in service_selectors]) > 0:
                exposed_obj.append(workload)
        return exposed_obj

    def find_svc_exposing_workload(self, kube_object: KubeWorkload):
        exposing_svc = []
        object_labels = kube_object.labels

        for svc in self.services:
            matching_labels = [l for l in object_labels.items() if l in svc.selectors.items()]
            if len(matching_labels) > 0:
                exposing_svc.append(svc)

        return exposing_svc

    def find_workload_defining_container(self, container_fullname: str):
        for workload in self.workloads:
            for container in workload.containers:
                search_container_fullname = f"{container.name}.{workload.typed_fullname}"
                if container_fullname == search_container_fullname:
                    return workload

    def get_object_by_name(self, object_name: str):
        objects_found = []
        for obj in self.cluster_objects:

            # Case: name is <name>.<namespace>.<svc> (or instead of svc something else)
            if obj.typed_fullname == object_name:
                if not obj in objects_found:
                    objects_found.append(obj)

            # Case: name is <name>.<namespace>
            #if obj.fullname == object_name:
            #    if not obj in objects_found:
            #        objects_found.append(obj)

            # Case: name is only <name>
            #if obj.name == object_name:
            #    if not obj in objects_found:
            #        objects_found.append(obj)

            # Case: name is a container name
            if isinstance(obj, KubeWorkload):
                for container in obj.containers:
                    if container.typed_fullname == object_name:
                        if not obj in objects_found:
                            objects_found.append(container)

        if len(objects_found) > 1:
            raise AttributeError(f"More than one object found with name: {object_name}")

        return objects_found[0] if objects_found else None
