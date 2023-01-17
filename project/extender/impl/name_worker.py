from microfreshener.core.model import MicroToscaModel, Service, Datastore, MessageRouter, MessageBroker, Compute

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import NAME_WORKER
from project.ignorer.impl.ignore_nothing import IgnoreNothing
from project.ignorer.ignorer import IgnoreType
from project.kmodel.kube_container import KubeContainer
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
                    # TODO Under the assumption that Service (or Datastore, MessageBorker) == Container, I can directly
                    # research in Container in order to specify even Service only with container name
                    if isinstance(node, Service) or isinstance(node, MessageBroker) or isinstance(node, Datastore):
                        # Node is directly name as a container
                        container = cluster.get_object_by_name(node.name, KubeContainer)
                        if container:
                            self._rename_node(model, node, container.typed_fullname)

                        # Node is named as the pod
                        workload = cluster.get_object_by_name(node.name, KubeWorkload)
                        if workload:
                            if len(workload.containers) == 1:
                                self._rename_node(model, node, workload.containers[0].typed_fullname)
                            else:
                                raise ValueError(f"Cannot determine which container is represented by node {node.name}. "
                                                 f"Please change its name in the model following the format "
                                                 f"container-name.name.namespace.type or ignore it")

                    if isinstance(node, Compute):
                        workload = cluster.get_object_by_name(node.name, KubeWorkload)
                        if workload:
                            self._rename_node(model, node, workload.typed_fullname)

                    if isinstance(node, MessageRouter):
                        k_service = cluster.get_object_by_name(node.name, KubeNetworking)

                        if k_service:
                            self._rename_node(model, node, k_service.typed_fullname)

        return model

    def _rename_node(self, model, node, new_name):
        if new_name != node.name:
            self.name_mapping[new_name] = node.name
            model.rename_node(node, new_name)
