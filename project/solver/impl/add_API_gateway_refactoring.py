from typing import List

from microfreshener.core.analyser.costants import REFACTORING_ADD_API_GATEWAY
from microfreshener.core.analyser.smell import NoApiGatewaySmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter, MessageBroker

from k8s_template.kobject_generators import generate_svc_NodePort_for_container, generate_ports_for_container_nodeport
from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.kmodel.kube_networking import KubeService
from project.kmodel.kube_utils import does_selectors_labels_match
from project.kmodel.kube_workload import KubeWorkload
from project.report.report_msg import cannot_apply_refactoring_on_node_msg, created_new_resource_msg, \
    existing_resource_modified_msg, removed_exposing_params_msg
from project.report.report_row import RefactoringStatus
from project.solver.pending_ops import PENDING_OPS
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class AddAPIGatewayRefactoring(Refactoring):
    # https://alesnosek.com/blog/2017/02/14/accessing-kubernetes-pods-from-outside-of-the-cluster/

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_ADD_API_GATEWAY)

    '''
    #TESI
    Viene estratto tutto (container, workload, porte da esporre del pod) e poi:
    - Se viene trovato un KubeService in grado già di esporre quel pod, allora viene utilizzato quello (le porte da esporre devono essere dipsonibili sul servizio).
        Il KubeService deve essere accessibile dall'esterno
    - Se non viene trovato alcun KubeService, allora ne viene creato uno nuovo
    '''
    def apply(self, smell: NoApiGatewaySmell):
        result = False
        refactoring_status, report_messages = None, []

        if not isinstance(smell, NoApiGatewaySmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        # Handle Message Broker case
            # The message broker is implemented through a Pod, so this case is the same as Service

        if isinstance(smell.node, Service) or isinstance(smell.node, MessageBroker):
            container, workload = self._get_container_and_def_object(smell.node.name)
            ports_to_expose = generate_ports_for_container_nodeport(workload, container, workload.host_network)
            expose_svc = self._search_for_existing_svc(workload, ports_to_expose)

            # Case: exists a Service that can expose this object
            if expose_svc and expose_svc.is_reachable_from_outside():
                expose_svc.ports.extend(ports_to_expose)
                self._refactor_model_service_exists(expose_svc, smell_node=smell.node)

                result = True
                report_messages.append(existing_resource_modified_msg(expose_svc.fullname, self.cluster.get_exp_object(expose_svc).out_fullname))
                refactoring_status = RefactoringStatus.SUCCESSFULLY_APPLIED

            # Case: need to create a new Service
            else:
                node_port_service = generate_svc_NodePort_for_container(
                    defining_obj=workload,
                    container=container,
                    is_host_network=workload.host_network
                )

                exp = ExportObject(node_port_service, None)
                self.cluster.add_object(node_port_service)
                self.cluster.add_export_object(exp)

                self._refactor_model_service_added(node_port_service, service_node=smell.node)

                result = True
                report_messages.append(created_new_resource_msg(node_port_service.fullname, exp.out_fullname))
                refactoring_status = RefactoringStatus.SUCCESSFULLY_APPLIED

            # Remove exposing parameters from Workload
            self._remove_exposing_attributes(workload, container)
            report_messages.append(removed_exposing_params_msg(workload.fullname, self.cluster.get_exp_object(workload).out_fullname))
        else:
            result = False
            report_messages.append(cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node))
            refactoring_status = RefactoringStatus.NOT_APPLIED

        self._add_report_row(smell, refactoring_status, report_messages)

        return result

    def _remove_exposing_attributes(self, workload: KubeWorkload, container: KubeContainer):
        if workload.host_network:
            if self.solver_pending_ops is not None:
                pending_action = (PENDING_OPS.REMOVE_WORKLOAD_HOST_NETWORK, workload)
                if not pending_action in self.solver_pending_ops:
                    self.solver_pending_ops.append(pending_action)
        else:
            for port in container.ports:
                if port.get("hostPort"):
                    del port["hostPort"]

    def _get_container_and_def_object(self, service_node_name: str):
        container = self.cluster.get_object_by_name(service_node_name)
        def_object = self.cluster.find_workload_defining_container(service_node_name) if container else None

        return container, def_object

    def _search_for_existing_svc(self, workload, ports_to_open):
        port_numbers = [p.get('node_port', p.get('port')) for p in ports_to_open]

        services = [s for s in self.cluster.services
                    if does_selectors_labels_match(s.selectors, workload.labels)
                    and self._check_ports(s, port_numbers)]

        if len(services) == 0:
            return None
        elif len(services) == 1:
            expose_svc = services[0]
        else:
            services = sorted(services, key=self.cluster.find_svc_exposing_workload)
            expose_svc = services[0]

        return expose_svc

    def _check_ports(self, svc, ports_to_check: List[int]):
        for svcport in svc.ports:
            exposed_port = svcport.get('node_port', svcport.get('port', None))
            if exposed_port and exposed_port in ports_to_check:
                return False

        return True

    def _refactor_model_service_exists(self, expose_svc: KubeService, smell_node: Service):
        message_router_node = self.model.get_node_by_name(expose_svc.typed_fullname)

        if message_router_node:
            self.model.edge.remove_member(smell_node)
            self.model.add_interaction(source_node=message_router_node, target_node=smell_node)
        else:
            return False

    def _refactor_model_service_added(self, node_port_service: KubeService, service_node):
        message_router_node = MessageRouter(node_port_service.typed_fullname)

        self.model.add_node(message_router_node)

        self.model.edge.remove_member(service_node)
        self.model.edge.add_member(message_router_node)

        self.model.add_interaction(source_node=message_router_node, target_node=service_node)




