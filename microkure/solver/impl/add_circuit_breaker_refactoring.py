from microfreshener.core.analyser.costants import REFACTORING_ADD_CIRCUIT_BREAKER
from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell, Smell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from microkure.template.kobject_generators import generate_circuit_breaker_for_svc
from microkure.ignorer.ignorer import IgnoreType
from microkure.ignorer.impl.ignore_nothing import IgnoreNothing
from microkure.kmodel.kube_cluster import KubeCluster
from microkure.kmodel.kube_networking import KubeService
from microkure.report.report import RefactoringReport
from microkure.report.messages import cannot_apply_refactoring_on_node_msg, found_wrong_type_object_msg, \
    created_resource_msg, handle_error_on_microservice
from microkure.report.report_row import RefactoringStatus
from microkure.solver.refactoring import RefactoringNotSupportedError, Refactoring


class AddCircuitBreakerRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_ADD_CIRCUIT_BREAKER)

    def apply(self, smell: Smell, ignorer=IgnoreNothing()):
        if not isinstance(smell, WobblyServiceInteractionSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        if ignorer.is_ignored(smell.node, IgnoreType.REFACTORING, self.name):
            return False

        if isinstance(smell.node, Service):
            for link in smell.links_cause:

                if isinstance(link.target, Service):
                    # This case is covered by refactoring. Running it multiple times, at some time in the model will be
                    # present a MessageRouter in front of this Service (AddMessageRouter) and this case will be covered
                    pass

                if isinstance(link.target, MessageRouter):
                    kube_service = self.cluster.get_object_by_name(link.target.name)

                    if not isinstance(kube_service, KubeService):
                        report_row = RefactoringReport().add_row(smell=smell, refactoring_name=self.name)
                        report_row.status = RefactoringStatus.NOT_APPLIED
                        report_row.add_message(found_wrong_type_object_msg(kube_service.fullname, KubeService.__class__.name))
                        return False

                    circuit_breaker = generate_circuit_breaker_for_svc(kube_service)
                    exp = self._add_to_cluster(circuit_breaker)

                    # Refactor model
                    self._refactor_model(link.target)

                    report_row = RefactoringReport().add_row(smell=smell, refactoring_name=self.name)
                    report_row.add_message(created_resource_msg(circuit_breaker, exp.out_fullname))
                    report_row.add_message(handle_error_on_microservice("circuit breaker", smell.node.name))
                    report_row.status = RefactoringStatus.PARTIALLY_APPLIED
            return True

        else:
            report_row = RefactoringReport().add_row(smell=smell, refactoring_name=self.name)
            report_row.status = RefactoringStatus.NOT_APPLIED
            report_row.add_message(cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node))
            return False

    def _refactor_model(self, mr_node):
        for link in mr_node.incoming_interactions:
            link.set_circuit_breaker(True)
