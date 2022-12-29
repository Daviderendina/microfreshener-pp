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
from project.report.report import RefactoringReport
from project.report.report_msg import cannot_apply_refactoring_on_node_msg, created_resource_msg, \
    resource_modified_msg, removed_exposing_params_msg, cannot_find_nodes_msg
from project.report.report_row import RefactoringStatus, RefactoringReportRow
from project.solver.pending_ops import PENDING_OPS
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class AddAPIGatewayRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_ADD_API_GATEWAY)

    def apply(self, smell: NoApiGatewaySmell):
        report_row: RefactoringReportRow = RefactoringReport().add_row(smell=smell)

        if not isinstance(smell, NoApiGatewaySmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        if isinstance(smell.node, Service) or isinstance(smell.node, MessageBroker):
            container = self.cluster.get_object_by_name(smell.node.name)
            workload = self.cluster.get_object_by_name(container.workload_typed_fullname) if container else None

            if container and workload:
                ports_to_expose = generate_ports_for_container_nodeport(container, workload.host_network)
                expose_svc = self._search_for_existing_svc(workload, ports_to_expose) #TODO RICERCA_SERVICE_DISPONIBILE

                # Case: exists a Service that can expose this object
                if expose_svc and expose_svc.is_reachable_from_outside():
                    expose_svc.ports.extend(ports_to_expose)
                    self._refactor_model(expose_svc, smell.node, service_exists=True)

                    # Update report row
                    export_object_fullname = self.cluster.get_exp_object(expose_svc).out_fullname
                    report_row.add_message(resource_modified_msg(expose_svc.fullname, export_object_fullname))
                    report_row.status = RefactoringStatus.SUCCESSFULLY_APPLIED

                    result = True

                # Case: need to create a new Service
                else:
                    node_port_service = generate_svc_NodePort_for_container(workload, container, workload.host_network)

                    exp = self._add_to_cluster(node_port_service)
                    self._refactor_model(node_port_service, smell.node, service_exists=False)

                    # Update report row
                    report_row.add_message(created_resource_msg(node_port_service.fullname, exp.out_fullname))
                    report_row.status = RefactoringStatus.SUCCESSFULLY_APPLIED

                    result = True

                # Remove exposing parameters from Workload and update report
                self._remove_exposing_attributes(workload, container)
                exp_object = self.cluster.get_exp_object(workload)
                exp_fullname = exp_object.out_fullname if exp_object else ""
                report_row.add_message(removed_exposing_params_msg(workload.fullname, exp_fullname))

            else:
                report_row.add_message(cannot_find_nodes_msg([smell.node.name, container.workload_typed_fullname]))
                report_row.status = RefactoringStatus.NOT_APPLIED
                result = False

        else:
            report_row.add_message(cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node))
            report_row.status = RefactoringStatus.NOT_APPLIED
            result = False

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

    def _add_to_cluster(self, object) -> ExportObject:
        exp = ExportObject(object, None)
        self.cluster.add_object(object)
        self.cluster.add_export_object(exp)

        return exp

    def _refactor_model(self, k_service: KubeService, node, service_exists: bool):
        mr_node = self.model.get_node_by_name(k_service.typed_fullname) if service_exists else MessageRouter(k_service.typed_fullname)

        if mr_node:
            if not service_exists:
                self.model.add_node(mr_node)
                self.model.edge.add_member(mr_node)

            self.model.edge.remove_member(node)
            self.model.add_interaction(source_node=mr_node, target_node=node)



#TODO RIVEDERE!!!
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

