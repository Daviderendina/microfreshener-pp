from abc import abstractmethod

from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Service

from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer
from project.kmodel.kPod import KPod


# TODO da rimuovere quando pubblico su pip il package
class Compute(Service):

    def __init__(self, name):
        super(Compute, self).__init__(name)

    def __str__(self):
        return '{} ({})'.format(self.name, 'compute')


# TODO i nomi non mi piacciono
class KubeWorker:

    @abstractmethod
    def refine(self, model: MicroToscaModel, kubecluster: KCluster) -> MicroToscaModel:
        pass


class IstioWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kubecluster: KCluster) -> MicroToscaModel:
        print("Starting Istio worker")


class ContainerWorker(KubeWorker):

    def refine(self, model: MicroToscaModel, kubecluster: KCluster) -> MicroToscaModel:
        print("Starting container worker")  # TODO logger
        for node in list(model.nodes):
            if isinstance(node, Service):
                kobject = kubecluster.get_object_by_name(node.name)

                if kobject is not None and isinstance(kobject, KPod):
                    self._add_compute_nodes(model=model, service_node=node, container_list=kobject.get_containers())
                else:
                    pod_template = kubecluster.get_pod_template_spec_by_name(node.name)
                    if pod_template is not None:
                        self._add_compute_nodes(model=model, service_node=node,
                                                container_list=pod_template.get_containers())

    def _add_compute_nodes(self, model: MicroToscaModel, service_node: Service, container_list: list[KContainer]):
        for container in container_list:
            # TODO qui ho avuto un problema con i nomi. Per ricrearlo, basta usare direttamente container.name al posto di compute_name
            # In pratica, avere un Service e un Compute node con lo stesso nome non è possibile.
            compute_name = container.name + "/" + service_node.name
            compute_node = Compute(compute_name)
            model.add_node(compute_node)
            model.add_interaction(source_node=service_node, target_node=compute_node)
