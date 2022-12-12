import re
from typing import List

from project.kmodel.kube_istio import KubeVirtualService, KubeDestinationRule, KubeIstioGateway
from project.kmodel.kube_networking import KubeService, KubeIngress
from project.kmodel.kube_workload import KubeWorkload


class KubeCluster:

    def __init__(self):
        self.cluster_objects = list()

    @property
    def workloads(self):
        return [obj for obj in self.cluster_objects if isinstance(obj, KubeWorkload)]

    @property
    def services(self):
        return [svc for svc in self.cluster_objects if isinstance(svc, KubeService)]

    @property
    def containers(self):
        return [(w.get_fullname(), w.get_containers()) for w in self.workloads]

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

    def find_workload_exposed_by_svc(self, service: KubeService) -> List[KubeWorkload]:
        exposed_obj = []
        for workload in self.workloads:
            service_selectors = [f"{k}:{v}" for k, v in service.get_selectors().items()]
            pod_labels = [f"{k}:{v}" for k, v in workload.get_labels().items()]
            if len([value for value in pod_labels if value in service_selectors]) > 0:
                exposed_obj.append(workload)
        return exposed_obj

    def find_svc_exposing_workload(self, kube_object: KubeWorkload):
        exposing_svc = []
        object_labels = kube_object.get_labels()

        for svc in self.services:
            matching_labels = [l for l in object_labels.items() if l in svc.get_selectors().items()]
            if len(matching_labels) > 0:
                exposing_svc.append(svc)

        return exposing_svc

    def find_workload_defining_container(self, container_fullname: str):
        for workload in self.workloads:
            for container in workload.get_containers():
                search_container_fullname = f"{container.name}.{workload.get_fullname()}"
                if container_fullname == search_container_fullname:
                    return workload

    def get_object_by_name(self, object_name: str):
        for obj in self.cluster_objects:

            # Case: name is FQDN
            result = re.match(obj.get_fullname() + r"[.][a-zA-Z]*[.]cluster[.]local", object_name)
            if result and result.string == object_name:
                return obj

            # Case: name is <name>.<namespace>
            if obj.get_fullname() == object_name:
                return obj

            # Case: name is only <name>
            possible = []
            if obj.name == object_name:
                possible.append(obj)
            if len(possible) == 1:
                return possible[0]

            # Case: name is a container name
            if isinstance(obj, KubeWorkload):
                for container in obj.get_containers():
                    container_fullname = f"{container.name}.{obj.get_fullname()}"
                    if container_fullname == object_name:
                        return container