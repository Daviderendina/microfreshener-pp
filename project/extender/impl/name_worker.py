from microfreshener.core.model import MicroToscaModel, Service, Datastore, MessageRouter, MessageBroker, Compute

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import NAME_WORKER
from project.ignorer.ignore_nothing import IgnoreNothing
from project.ignorer.ignorer import IgnoreType
from project.kmodel.shortnames import ALL_SHORTNAMES


class NameWorker(KubeWorker):

    ERROR_NOT_FOUND = "Not found corrispondence with name {name} in the cluster"
    MULTIPLE_FOUND = "Found correspondence with {number} object in the cluster with name {name}. Please specify shortname in the toscaMODEL"

    def __init__(self):
        super().__init__(NAME_WORKER)

    def refine(self, model, cluster, ignorer=IgnoreNothing()) -> MicroToscaModel:
        for node in list(model.nodes):
            if not ignorer.is_ignored(node, IgnoreType.WORKER, self.name):

                if node.name.split(".")[-1] in ALL_SHORTNAMES:
                    if len([n for n in cluster.cluster_objects if n.typed_fullname == node.name]) == 0:
                        raise ValueError(self.ERROR_NOT_FOUND.format(name=node.name))

                else:
                    if isinstance(node, Compute) or isinstance(node, Service) or isinstance(node, MessageBroker) or isinstance(node, Datastore):
                        workloads = [w for w in cluster.workloads if w.fullname == node.name]

                        if len(workloads) == 1:
                            model.rename_node(node, workloads[0].typed_fullname)
                        elif len(workloads) > 1:
                            raise ValueError(self.MULTIPLE_FOUND.format(len(workloads), node.name))
                        else:
                            # Check for containers
                            for workload in cluster.workloads:
                                for container in workload.containers:
                                    if container.fullname == node.name:
                                        model.rename_node(node, container.typed_fullname)

                    if isinstance(node, MessageRouter):
                        networkings = [n for n in cluster.networkings if n.fullname == node.name]

                        if len(networkings) == 1:
                            model.rename_node(node, networkings[0].typed_fullname)
                        elif len(networkings) > 1:
                            raise ValueError(self.MULTIPLE_FOUND.format(len(networkings), node.name))

        return model
