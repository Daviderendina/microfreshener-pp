import uuid

from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service

from k8s_template.kobject_generators import generate_ports_for_container, generate_svc_clusterIP_for_container
from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kobject_kind import KObjectKind
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError
from project.utils import check_ports_match


class AddMessageRouterRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):

        if not isinstance(smell, EndpointBasedServiceInteractionSmell):
            raise RefactoringNotSupportedError

        if isinstance(smell.node, Service):
            smell_container: KContainer = self.cluster.get_container_by_tosca_model_name(service_name=smell.node.name)

            if smell_container is None:
                return

            defining_object_fullname: str = smell.node.name[len(smell_container.name) + 1:]
            defining_object: KObject = self.cluster.get_object_by_name(defining_object_fullname)

            if defining_object is not None:
                exposing_service = self.cluster.find_services_which_expose_object(defining_object)

                if len(exposing_service) > 0:
                    port_compatible_services = [s for s in exposing_service if check_ports_match(s, smell_container)]

                    if len(port_compatible_services) > 0:
                        port_compatible_services.sort(key=lambda svc:
                                      len(self.cluster.find_pods_exposed_by_service(svc)) +
                                      len(self.cluster.find_defining_obj_exposed_by_service(svc)))

                        container_ports = generate_ports_for_container(
                            container=smell_container,
                            defining_obj=defining_object)
                        port_compatible_services[0].spec.ports += container_ports
                    else:
                        #TODO se arrivo qui le porte non sono compatibili, ma devo capire una cosa: la porta che già espone
                        # è di quel pod oppure di altro? Questo va fatto nell'extender
                        generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=defining_object)
                        self.cluster.add_object(generated_service, KObjectKind.SERVICE)

                else:
                    generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=defining_object)
                    self.cluster.add_object(generated_service, KObjectKind.SERVICE)

            # Lo sviluppatore deve in qualche modo confermare di aver cambiato le chiamate, dall'IP al nome del svc
            # (il nome lo prendo direttamente dal pod/deploy/etc..) TODO

