from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel

from project.ignorer.ignore_config import IgnoreConfig, IgnoreType
from project.ignorer.ignore_nothing import IgnoreNothing
from project.ignorer.ignorer import Ignorer
from project.kmodel.kube_cluster import KubeCluster


class KubeWorker:

    def __init__(self, name):
        self.executed_only_after_workers = []
        self.name = name

    @abstractmethod
    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig) -> MicroToscaModel:
        pass

    def _get_nodes_not_ignored(self, nodes, ignore: Ignorer):
        if ignore is None:
            ignore = IgnoreNothing()

        return [n for n in nodes if not ignore.is_node_ignored(n, IgnoreType.WORKER, self.name)]
