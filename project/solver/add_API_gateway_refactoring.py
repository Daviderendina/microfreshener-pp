from microfreshener.core.analyser.smell import Smell, NoApiGatewaySmell
from microfreshener.core.model import MicroToscaModel, Service

from k8s_template.kobject_generators import generate_svc_NodePort_for_container
from k8s_template.service_template import generate_service_from_template
from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer
from project.kmodel.kobject_kind import KObjectKind
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError


class AddAPIGatewayRefactoring(Refactoring):
    # https://alesnosek.com/blog/2017/02/14/accessing-kubernetes-pods-from-outside-of-the-cluster/
    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, NoApiGatewaySmell):
            raise RefactoringNotSupportedError

        # Handle Message Broker case
            #TODO per me non si può fare

        # Handle service case
            #TODO non devo controllare che non ci sia già qualcosa?
        if isinstance(smell.node, Service):
            container, def_object = self._get_container_and_def_object(smell.node.name)

            node_port_service = generate_svc_NodePort_for_container(
                defining_obj=def_object,
                container=container,
                is_host_network=def_object.is_host_network()
            )

            self.cluster.add_object(node_port_service, KObjectKind.SERVICE)

    def _get_container_and_def_object(self, service_node_name: str):
        container = self.cluster.get_container_by_tosca_model_name(service_node_name)
        if container:
            def_object = self.cluster.get_container_defining_object(container)

        return container, def_object



