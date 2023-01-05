from microfreshener.core.model import MicroToscaModel, Service, Datastore, MessageRouter, MessageBroker, Compute

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import NAME_WORKER
from project.ignorer.impl.ignore_nothing import IgnoreNothing
from project.ignorer.ignorer import IgnoreType
from project.kmodel.kube_networking import KubeNetworking
from project.kmodel.kube_workload import KubeWorkload
from project.kmodel.shortnames import ALL_SHORTNAMES


class NameWorker(KubeWorker):

    ERROR_NOT_FOUND = "Not found corrispondence with name {name} in the cluster"
    MULTIPLE_FOUND = "Found correspondence with {number} object in the cluster with name {name}. Please specify shortname in the toscaMODEL"

    def __init__(self):
        super().__init__(NAME_WORKER)
        self.name_mapping = {}  # Map the new name given to the nome with the old name

    def refine(self, model, cluster, ignorer=IgnoreNothing()) -> MicroToscaModel:
        for node in list(model.nodes):
            if not ignorer.is_ignored(node, IgnoreType.WORKER, self.name):

                if node.name.split(".")[-1] in ALL_SHORTNAMES:
                    if len([n for n in cluster.cluster_objects + cluster.containers if n.typed_fullname == node.name]) == 0:
                        raise ValueError(self.ERROR_NOT_FOUND.format(name=node.name))

                else:
                    if isinstance(node, Compute) or isinstance(node, Service) or isinstance(node, MessageBroker) or isinstance(node, Datastore):
                        workload = cluster.get_object_by_name(node.name, KubeWorkload)

                        if workload:
                            self._rename_node(model, node, workload.typed_fullname)
                        else:
                            # Check for containers
                            for workload in cluster.workloads:
                                for container in workload.containers:
                                    if container.fullname == node.name:
                                        self._rename_node(model, node, container.typed_fullname)

                    if isinstance(node, MessageRouter):
                        k_service = cluster.get_object_by_name(node.name, KubeNetworking)

                        if k_service:
                            self._rename_node(model, node, k_service.typed_fullname)

        return model

    def _rename_node(self, model, node, new_name):
        self.name_mapping[new_name] = node.name
        model.rename_node(node, new_name)
