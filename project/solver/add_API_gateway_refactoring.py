from microfreshener.core.analyser.smell import Smell, NoApiGatewaySmell
from microfreshener.core.model import MicroToscaModel, Service

from k8s_template.kobject_generators import generate_svc_NodePort_for_container, generate_ports_for_container_nodeport
from project.kmodel.kCluster import KCluster
from project.kmodel.kObject import KObject
from project.kmodel.kService import KService
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

        if isinstance(smell.node, Service):
            container, def_object = self._get_container_and_def_object(smell.node.name)

            ports_to_expose = generate_ports_for_container_nodeport(
                def_object, container, def_object.is_host_network()
            )
            expose_svc = self._search_for_existing_svc(def_object, ports_to_expose)
            if expose_svc:
                svc_ports = expose_svc.get_ports()
                svc_ports += ports_to_expose

            else:
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

    def _search_for_existing_svc(self, defining_obj: KObject, ports_to_open: list[int]):
        port_numbers = [p.get('node_port', p.get('port')) for p in ports_to_open]
        services = [s for s in self.cluster.find_services_which_expose_object(defining_obj)
                    if self._check_ports(s, port_numbers)]

        if len(services) == 0:
            return None
        elif len(services) == 1:
            expose_svc = services[0]
        else:
            services = sorted(services, key=self.cluster.find_services_which_expose_object)
            expose_svc = services[0]

        return expose_svc

    def _check_ports(self, svc: KService, ports_to_check: list[int]):
        for svcport in svc.get_ports():
            port = svcport.get('node_port', svcport.get('port', None))
            if port and port in ports_to_check:
                return False

        return True



