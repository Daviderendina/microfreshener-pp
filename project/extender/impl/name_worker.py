from microfreshener.core.model import MicroToscaModel, Service, Datastore, MessageRouter, MessageBroker, Compute, Root

from project.constants import WorkerNames
from project.extender.kubeworker import KubeWorker
from project.ignorer.ignore_config import IgnoreConfig
from project.ignorer.ignorer import IgnoreType
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.shortnames import ALL_SHORTNAMES


class NameWorker(KubeWorker):

    def __init__(self):
        super().__init__(WorkerNames.NAME_WORKER)

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig) -> MicroToscaModel:
        for node in list(model.nodes):
            if not ignore.is_node_ignored(node, IgnoreType.WORKER, self.name):

                if node.name.split(".")[-1] in ALL_SHORTNAMES:
                    if len([n for n in kube_cluster.cluster_objects if n.typed_fullname == node.name]) == 0:
                        raise ValueError(f"Not found corrispondence with name {node.name} in the cluster")
                else:
                    if isinstance(node, Compute) or isinstance(node, Service) or isinstance(node, MessageBroker) or isinstance(node, Datastore):
                        #TODO i container se rinominati bene rimangono fuori da ciò
                        #TODO i MB abbiamo detto che li considero come Pod!
                        workloads = [w for w in kube_cluster.workloads if w.fullname == node.name]

                        if len(workloads) == 1:
                            #node.name = workloads[0].typed_fullname
                            model.rename_node(node, workloads[0].typed_fullname)
                        elif len(workloads) > 1:
                            raise ValueError(f"Found correspondence with {len(workloads)} object in the cluster with name {node.name}. Please specify shortname in the toscaMODEL")
                        else:
                            # Check for containers
                            for workload in kube_cluster.workloads:
                                for container in workload.containers:
                                    if container.fullname == node.name:
                                        model.rename_node(node, container.typed_fullname)

                    if isinstance(node, MessageRouter):
                        networkings = [n for n in kube_cluster.networkings if n.fullname == node.name]
                        if len(networkings) == 1:
                            #node.name = networkings[0].typed_fullname
                            model.rename_node(node, networkings[0].typed_fullname)
                        elif len(networkings) > 1:
                            raise ValueError(f"Found correspondence with {len(networkings)} object in the cluster with name {node.name}. Please specify shortname in the toscaMODEL")


        return model
