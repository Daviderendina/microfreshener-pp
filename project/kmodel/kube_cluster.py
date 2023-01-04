
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
        return [container for sublist in [w.containers for w in self.workloads] for container in sublist]

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
        return [w for w in self.workloads if service.does_expose_workload(w)]

    def find_svc_exposing_workload(self, workload: KubeWorkload):
        return [s for s in self.services if s.does_expose_workload(workload)]

    def get_object_by_name(self, object_name: str, type: type = None):
        #TODO potrebbe arrivarmi anche un FQDN!! da _search_for_circuit_breaker
        objects_found = []
        for obj in self.cluster_objects:

            # Case: name is <name>.<namespace>.<svc> (or instead of svc something else)
            if obj.typed_fullname == object_name:
                if not obj in objects_found:
                    objects_found.append(obj)

            # Case: name is <name>.<namespace>
            if obj.fullname == object_name:
                if not obj in objects_found:
                    objects_found.append(obj)

            # Case: name is a container name
            if isinstance(obj, KubeWorkload):
                for container in obj.containers:
                    if container.typed_fullname == object_name:
                        if not obj in objects_found:
                            objects_found.append(container)

        if type is not None:
            objects_found = [o for o in objects_found if isinstance(o, type)]

        if len(objects_found) > 1:
            raise AttributeError(f"More than one object found with name: {object_name}")

        return objects_found[0] if objects_found else None

    def get_exp_object(self, kube_object):
        for obj in self.cluster_export_info:
            if obj.kube_object == kube_object:
                return obj