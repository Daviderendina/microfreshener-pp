from microfreshener.core.analyser.costants import REFACTORING_ADD_CIRCUIT_BREAKER
from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell, Smell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_circuit_breaker_for_svc
from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.report.report_msg import cannot_apply_refactoring_on_node_msg, found_wrong_type_object_msg, \
    created_new_resource_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class AddCircuitBreakerRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_ADD_CIRCUIT_BREAKER)

    def apply(self, smell: Smell):
        if not isinstance(smell, WobblyServiceInteractionSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        if isinstance(smell.node, Service):
            for link in smell.links_cause:

                if isinstance(link.target, Service):
                    # This case is covered by refactoring. Running it multiple times, at some time in the model will be
                    # present a MessageRouter in front of this Service (AddMessageRouter) and this case will be covered
                    pass

                if isinstance(link.target, MessageRouter):
                    kube_service = self.cluster.get_object_by_name(link.target.name)

                    if not isinstance(kube_service, KubeService):
                        msg = found_wrong_type_object_msg(kube_service.fullname, KubeService.__class__.name)
                        self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, msg)
                        return False

                    circuit_breaker = generate_circuit_breaker_for_svc(kube_service)

                    exp = ExportObject(circuit_breaker, None)
                    self.cluster.add_object(circuit_breaker)
                    self.cluster.add_export_object(exp)

                    # Refactor model
                    self._refactor_model(link.target)

                    msg = created_new_resource_msg(circuit_breaker.fullname, exp.out_fullname)
                    self._add_report_row(smell, RefactoringStatus.SUCCESSFULLY_APPLIED, msg)
                    return True
        else:
            msg = cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node)
            self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, msg)
            return False

    def _refactor_model(self, mr_node):
        for link in mr_node.incoming_interactions:
            link.set_circuit_breaker(True)
