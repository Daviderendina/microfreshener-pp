from microfreshener.core.analyser.costants import REFACTORING_ADD_MESSAGE_ROUTER
from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_svc_clusterIP_for_container
from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.report.report_msg import cannot_find_container_msg, cannot_apply_refactoring_on_node_msg, \
    change_call_to_service_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class AddMessageRouterRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_ADD_MESSAGE_ROUTER)

    def apply(self, smell: Smell):

        if not isinstance(smell, EndpointBasedServiceInteractionSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        if isinstance(smell.node, Service):
            smell_container: KubeContainer = self.cluster.get_object_by_name(smell.node.name)

            if smell_container is None:
                self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, cannot_find_container_msg(smell.node.name))
                return False

            workload_object = self.cluster.get_object_by_name(smell.node.name[len(smell_container.name) + 1:])
            # exposing_svc = self._find_compatible_exposing_service(workload_object, smell_container)
            #
            # if exposing_svc:
            #     model_result = self._refactor_model(smell.node, exposing_svc.fullname, smell.links_cause, svc_exists=True)
            #     if model_result:
            #         container_ports = generate_ports_for_container(
            #             container=smell_container,
            #             defining_obj=workload_object)
            #         exposing_svc.data["spec"]["ports"] += container_ports
            #
            #         self._add_report_row(smell, RefactoringStatus.PARTIALLY_APPLIED,
            #                              change_call_to_service_msg(smell.node.name, exposing_svc.typed_fullname))
            #         return True
            #     else:
            #         self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, cannot_refactor_model_msg())
            #         return False
            #
            # else:
            #     #TODO se arrivo qui (se non trovo porte compatibili per il pod durante la ricerca) le porte non sono compatibili, ma devo capire una cosa: la porta che già espone
            #     # è di quel pod oppure di altro? Questo va fatto nell'extender - forse vedendo i file vecchi si capisce meglio cosa intendo

            generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=workload_object)
            #model_result = \
            self._refactor_model(smell.node, generated_service.typed_fullname, smell.links_cause)

            #if model_result:
            self.cluster.add_object(generated_service)
            self.cluster.add_export_object(ExportObject(generated_service, None))

            report_msg = change_call_to_service_msg(smell.node.name, generated_service.fullname)
            refactoring_status, result = RefactoringStatus.PARTIALLY_APPLIED, True
            # else:
            #     report_msg = cannot_refactor_model_msg()
            #     refactoring_status, result = RefactoringStatus.NOT_APPLIED, False
        else:
            report_msg = cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node)
            refactoring_status, result = RefactoringStatus.NOT_APPLIED, False

        self._add_report_row(smell, refactoring_status, report_msg)
        return result
    #
    # def _find_compatible_exposing_service(self, workload, container):
    #     selected_service = None
    #
    #     exposing_service = [s for s in self.cluster.services if does_selectors_labels_match(s.selectors, workload.labels)]
    #
    #     if len(exposing_service) > 0:
    #         port_compatible_services = [s for s in exposing_service if self._check_ports_single_match(s, container)]
    #
    #         if len(port_compatible_services) > 0:
    #             port_compatible_services.sort(key=lambda svc: len(self.cluster.find_workload_exposed_by_svc(svc)))
    #
    #             selected_service = port_compatible_services[0]
    #
    #     return selected_service
    #
    # def _check_ports_single_match(self, service, container):
    #     #TODO ho spostato da utils il metodo qui, ma ora spacca. C'è da dire che il metodo di prima tonrava sempre true,
    #     # c'è proprio da rivedere anche il test e il funzionamento del refactorer.
    #     # Sarebbe carico estrarre la funzione da KubeService di ricerca del match delle porte e metterla in kube_utils,
    #     # Così da usare solo quella per vedere se effettivamente le porta matchano
    #     c_ports = [p.get("containerPort", "") for p in container.ports]
    #     s_ports = [p.get("targetPort", "") for p in service.ports]
    #
    #     return len([c for c in c_ports if c in s_ports]) > 0

    def _refactor_model(self, smell_node: Service, exposing_svc_name: str, smell_links):
        message_router = MessageRouter(exposing_svc_name)
        self.model.add_node(message_router)

        for interaction in smell_links:
            self.model.add_interaction(source_node=interaction.source, target_node=message_router)
            self.model.delete_relationship(interaction)

        # Search if relations between MR and Service also exists
        if len([r for r in message_router.interactions if r.target == smell_node and r.source == message_router]) == 0:
            self.model.add_interaction(source_node=message_router, target_node=smell_node)






