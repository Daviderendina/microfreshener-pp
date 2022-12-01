import uuid

from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service

from k8s_template.service_template import generate_port_from_template, generate_service_from_template
from project.kmodel.kCluster import KCluster
from project.kmodel.kContainer import KContainer
from project.kmodel.kObject import KObject
from project.kmodel.kPod import KPod
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError


class AddMessageRouterRefactoring(Refactoring):

    svc_name_suffix = "-svc-MF"

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        # TODO fare il tutto funzionante anche per Deployment, etc..

        if not isinstance(smell, EndpointBasedServiceInteractionSmell):
            raise RefactoringNotSupportedError

        if isinstance(smell.node, Service):
            smell_container: KContainer = self.cluster.get_container_by_tosca_model_name(service_name=smell.node.name)

            if smell_container is None:
                return

            defining_object_fullname: str = smell.node.name[len(smell_container.name) + 1:]
            defining_object: KObject = self.cluster.get_object_by_name(defining_object_fullname)

            if defining_object is not None:
                exposing_service = self.cluster.find_service_which_expose_object(defining_object)

                if len(exposing_service) > 0:
                    port_compatible_services = [s for s in exposing_service if self._check_port_compatibility(s, smell_container)]

                    if len(port_compatible_services) > 0:
                        port_compatible_services.sort(key=lambda svc:
                                      len(self.cluster.find_pods_exposed_by_service(svc)) +
                                      len(self.cluster.find_defining_obj_exposed_by_service(svc)))

                        container_ports = self._generate_ports_from_container(
                            container=smell_container,
                            defining_object_fullname=defining_object_fullname)
                        port_compatible_services[0].spec.ports += container_ports
                    else:
                        #TODO se arrivo qui le porte non sono compatibili, ma devo capire una cosa: la porta che già espone
                        # è di quel pod oppure di altro? Questo va fatto nell'extender
                        generated_service = self._create_service_for_container(defining_object, smell_container)
                        self.cluster.add_object(generated_service, KObjectKind.SERVICE)

                else:
                    generated_service = self._create_service_for_container(defining_object, smell_container)
                    self.cluster.add_object(generated_service, KObjectKind.SERVICE)

            # Lo sviluppatore deve in qualche modo confermare di aver cambiato le chiamate, dall'IP al nome del svc
            # (il nome lo prendo direttamente dal pod/deploy/etc..) TODO

    def _generate_ports_from_container(self, container: KContainer, defining_object_fullname: str) -> list:
        ports = []
        for port in container.ports:
            default_port_name = f"{defining_object_fullname}-port-{port['containerPort']}-MF"
            port = generate_port_from_template(
                    name=port.get("name", default_port_name),
                    port=port.get("containerPort"),
                    protocol=port.get("protocol", None),
                    target_port=port.get("targetPort", None)
                )
            ports.append(port)
        return ports

    def _create_service_for_container(self, defining_object: KObject, container: KContainer) -> KService:
        container_ports: list = self._generate_ports_from_container(container, defining_object.get_fullname())
        service_selector = {f"{defining_object.get_fullname()}{self.svc_name_suffix}": uuid.uuid4()}

        # Create a new service
        service = generate_service_from_template(
            name= f"{defining_object.metadata.name}{self.svc_name_suffix}", #TODO il nome che c'è già? lo scarto?
            namespace= defining_object.get_namespace(),
            selector_labels=service_selector,
            ports= container_ports
        )

        if isinstance(defining_object, KPod):
            defining_object.set_labels(service_selector)
        else:
            defining_object.get_pod_template_spec().set_labels(service_selector)

        return service

    def _check_port_compatibility(self, service: KService, container: KContainer):
        #service_ports = [p.get("port", "-1") for p in service.get_ports()]

        service_ports = []
        for port in service.get_ports():
            port.get("get", "-1")

        for port in container.ports:
            if port["containerPort"] in service_ports:
                return False
        return True




