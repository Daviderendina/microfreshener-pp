from microfreshener.core.analyser.costants import REFACTORING_ADD_MESSAGE_ROUTER
from microfreshener.core.analyser.smell import Smell, EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_svc_clusterIP_for_container
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_container import KubeContainer
from project.report.report_msg import cannot_find_container_msg, cannot_apply_refactoring_on_node_msg, \
    change_call_to_service_msg, created_resource_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class AddMessageRouterRefactoring(Refactoring):
    # TODO manca da fare il caso in cui il servizio ci sia già per il workload, ma forse è meglio prima pensare a un refactoring generale
    # Attenzione alle porte! Io già nell'extender controllo che le porte esposte siano corrette, perciò se non c'è la
    # freccia significa che le porte NON SONO ESPOSTE DAL SERVIZIO

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

            workload = smell_container.defining_workload
            generated_service = generate_svc_clusterIP_for_container(container=smell_container, defining_obj=workload)
            exp = self._add_to_cluster(generated_service)

            self._refactor_model(smell.node, generated_service.typed_fullname, smell.links_cause)

            msgs = [change_call_to_service_msg(smell.node.name, generated_service.fullname),
                    created_resource_msg(generated_service, exp.out_fullname)]
            self._add_report_row(smell, RefactoringStatus.PARTIALLY_APPLIED, msgs)
            return True
        else:
            report_msg = cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node)
            self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, report_msg)
            return False

    def _refactor_model(self, smell_node: Service, exposing_svc_name: str, smell_links):
        message_router = MessageRouter(exposing_svc_name)
        self.model.add_node(message_router)

        for interaction in smell_links:
            self.model.add_interaction(source_node=interaction.source, target_node=message_router)
            self.model.delete_relationship(interaction)

        # Search if relations between MR and Service also exists
        if len([r for r in message_router.interactions if r.target == smell_node and r.source == message_router]) == 0:
            self.model.add_interaction(source_node=message_router, target_node=smell_node)







