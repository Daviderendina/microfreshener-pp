from microfreshener.core.model import MicroToscaModel, MessageRouter

from project.extender.kubeworker import KubeWorker
from project.extender.worker_names import INGRESS_WORKER
from project.ignorer.ignore_config import IgnoreConfig
from project.ignorer.ignore_nothing import IgnoreNothing
from project.ignorer.ignorer import IgnoreType
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService, KubeIngress
from project.utils.utils import check_kobject_node_name_match


class IngressWorker(KubeWorker):

    def __init__(self):
        super().__init__(INGRESS_WORKER)
        self.model = None
        self.cluster = None

    def refine(self, model: MicroToscaModel, kube_cluster: KubeCluster, ignore: IgnoreConfig):
        self.model = model
        self.cluster = kube_cluster

        if not ignore:
            ignore = IgnoreNothing()

        for ingress in self.cluster.ingress:
            ingress_node = self.model.get_node_by_name(ingress.fullname, MessageRouter)

            if ingress_node:
                if not ignore.is_node_ignored(ingress_node, IgnoreType.WORKER, self.name):
                    self._handle_ingress_in_model(ingress, ingress_node, ignore)
            else:
                self._handle_ingress_not_in_model(ingress, ignore)

    def _handle_ingress_not_in_model(self, ingress: KubeIngress, ignore):
        for k_service_name in ingress.get_exposed_svc_names():

            k_services = [s for s in self.cluster.services if
                          s.fullname == k_service_name + "." + ingress.namespace]

            if len(k_services) > 0:
                not_ignored_nodes = self._get_nodes_not_ignored(list(self.model.nodes), ignore)
                mr_nodes = [n for n in not_ignored_nodes if check_kobject_node_name_match(k_services[0], n)]

                if len(mr_nodes) > 0:
                    mr_node = mr_nodes[0]
                    kube_service: KubeService = self.cluster.get_object_by_name(mr_node.name)
                    if kube_service and not kube_service.is_reachable_from_outside():
                        self.model.edge.remove_member(mr_node)

                    ingress_node = MessageRouter(ingress.typed_fullname)
                    self.model.add_node(ingress_node)
                    self.model.edge.add_member(ingress_node)
                    self.model.add_interaction(source_node=ingress_node, target_node=mr_node)

    def _handle_ingress_in_model(self, ingress: KubeIngress, ingress_node: MessageRouter, ignore):
        for exposed_svc in ingress.get_exposed_svc_names():
            mr_node = self.model.get_node_by_name(exposed_svc, MessageRouter)
            if mr_node not in [r.target for r in ingress_node.interactions]:
                if not ignore.is_node_ignored(mr_node, IgnoreType.WORKER, self.name):

                    self.model.add_interaction(source_node=ingress_node, target_node=mr_node)

