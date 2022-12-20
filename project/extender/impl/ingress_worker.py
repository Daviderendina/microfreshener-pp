from microfreshener.core.model import MicroToscaModel, MessageRouter, Edge

from project.constants import WorkerNames
from project.extender.kubeworker import KubeWorker
from project.ignorer.ignore_config import IgnoreConfig
from project.ignorer.ignore_nothing import IgnoreNothing
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.utils.utils import check_kobject_node_name_match


class IngressWorker(KubeWorker):

    def __init__(self):
        super().__init__(WorkerNames.INGRESS_WORKER)
        self.model = None
        self.cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig):
        self.model = model
        self.cluster = kube_cluster

        if not ignore:
            ignore = IgnoreNothing()

        for ingress in self.cluster.ingress:
            for k_service_name in ingress.get_exposed_svc_names():

                k_services = [s for s in self.cluster.services if s.fullname == k_service_name + "." + ingress.namespace]

                if len(k_services) > 0:
                    not_ignored_nodes = self._get_nodes_not_ignored(list(self.model.nodes), ignore)
                    mr_nodes = [n for n in not_ignored_nodes if check_kobject_node_name_match(k_services[0], n)]

                    if len(mr_nodes) > 0:
                        mr_node = mr_nodes[0]
                        kube_service: KubeService = kube_cluster.get_object_by_name(mr_node.name)
                        if kube_service and not kube_service.is_reachable_from_outside():
                            model.edge.remove_member(mr_node)

                        ingress_node = MessageRouter(ingress.fullname)
                        model.add_node(ingress_node)
                        model.edge.add_member(ingress_node)
                        model.add_interaction(source_node=ingress_node, target_node=mr_node)






