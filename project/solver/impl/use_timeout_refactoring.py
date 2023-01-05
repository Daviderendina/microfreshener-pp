from microfreshener.core.analyser.costants import REFACTORING_USE_TIMEOUT
from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell, Smell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_timeout_virtualsvc_for_svc
from project.kmodel.kube_cluster import KubeCluster
from project.report.report_msg import cannot_apply_refactoring_on_node_msg, created_resource_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class UseTimeoutRefactoring(Refactoring):
    DEFAULT_TIMEOUT_SEC = 2

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_USE_TIMEOUT)

    def apply(self, smell: Smell):
        if not isinstance(smell, WobblyServiceInteractionSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        if isinstance(smell.node, Service):
            for link in smell.links_cause:

                if not link.timeout:
                    if isinstance(link.target, Service):
                        pass
                        # This tool execute the whole process of finding smell ad refactoring multiple times, so this case
                        # will be solved when AddMessageRouter will add a MR in front of the smell node

                    if isinstance(link.target, MessageRouter):
                        k_service = self.cluster.get_object_by_name(link.target.name)

                        virtual_service = generate_timeout_virtualsvc_for_svc(k_service, self.DEFAULT_TIMEOUT_SEC)
                        exp = self._add_to_cluster(virtual_service)

                        # Refactor model
                        for up_interaction in link.target.incoming_interactions:
                            up_interaction.set_timeout(True)

                        msg = created_resource_msg(virtual_service, exp.out_fullname)
                        self._add_report_row(smell, RefactoringStatus.SUCCESSFULLY_APPLIED, msg)
                        return True
        else:
            msg = cannot_apply_refactoring_on_node_msg(self.name, smell.name, smell.node)
            self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, msg)
            return False
