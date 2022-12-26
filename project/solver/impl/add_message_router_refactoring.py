from microfreshener.core.analyser.costants import REFACTORING_ADD_MESSAGE_ROUTER
from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_ports_for_container, generate_svc_clusterIP_for_container
from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.report.report_msg import cannot_find_container_msg, cannot_apply_refactoring_on_node_msg, \
    change_call_to_service_msg, cannot_refactor_model_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring
from project.utils.utils import check_ports_match


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
            exposing_svc = self._find_compatible_exposing_service(workload_object, smell_container)

            if exposing_svc:
                model_result = self._refactor_model(smell.node, exposing_svc.fullname, smell.links_cause, svc_exists=True)
                if model_result:
                    container_ports = generate_ports_for_container(
                        container=smell_container,
                        defining_obj=workload_object)
                    exposing_svc.data["spec"]["ports"] += container_ports

                    self._add_report_row(smell, RefactoringStatus.PARTIALLY_APPLIED,
                                         change_call_to_service_msg(smell.node.name, exposing_svc.fullname))
                    return True
                else:
                    self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, cannot_refactor_model_msg())
                    return False

            else:
                #TODO se arrivo qui (se non trovo porte compatibili per il pod durante la ricerca) le porte non sono compatibili, ma devo capire una cosa: la porta che già espone
                # è di quel pod oppure di altro? Questo va fatto nell'extender - forse vedendo i file vecchi si capisce meglio cosa intendo

                generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=workload_object)
                model_result = self._refactor_model(smell.node, generated_service.typed_fullname, smell.links_cause, svc_exists=False)

                if model_result:
                    self.cluster.add_object(generated_service)
                    self.cluster.add_export_object(ExportObject(generated_service, None))

                    self._refactor_model(smell.node, generated_service.typed_fullname, smell.links_cause, svc_exists=False)

                    self._add_report_row(smell, RefactoringStatus.PARTIALLY_APPLIED,
                                         change_call_to_service_msg(smell.node.name, generated_service.fullname))
                    return True
                else:
                    self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, cannot_refactor_model_msg())
                    return False

        else:
            self._add_report_row(smell, RefactoringStatus.NOT_APPLIED,
                                 cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node))
            return False

    def _find_compatible_exposing_service(self, workload, container):
        selected_service = None

        exposing_service = self.cluster.find_svc_exposing_workload(workload)

        if len(exposing_service) > 0:
            port_compatible_services = [s for s in exposing_service if check_ports_match(s, container)]

            if len(port_compatible_services) > 0:
                port_compatible_services.sort(key=lambda svc: len(self.cluster.find_workload_exposed_by_svc(svc)))

                selected_service = port_compatible_services[0]

        return selected_service

    def _refactor_model(self, smell_node: Service, exposing_svc_name: str, smell_links, svc_exists: bool):
        message_router = self.model.get_node_by_name(exposing_svc_name, MessageRouter) \
            if svc_exists else MessageRouter(exposing_svc_name)

        if message_router:
            if not svc_exists:
                self.model.add_node(message_router)

            for interaction in smell_links:
                self.model.add_interaction(source_node=interaction.source, target_node=message_router)
                self.model.delete_relationship(interaction)

            # Search if relations between MR and Service also exists
            if len([r for r in message_router.interactions if r.target == smell_node and r.source == message_router]) == 0:
                self.model.add_interaction(source_node=message_router, target_node=smell_node)

            return True

        return False





