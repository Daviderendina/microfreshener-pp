import copy

from microfreshener.core.analyser.costants import REFACTORING_SPLIT_SERVICES
from microfreshener.core.analyser.smell import Smell, MultipleServicesInOneContainerSmell
from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute, Service

from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.report.report_msg import compute_object_not_found_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class SplitServicesRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_SPLIT_SERVICES)

    def apply(self, smell: Smell):
        if not isinstance(smell, MultipleServicesInOneContainerSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        compute_node: Compute = smell.node
        compute_object = self.cluster.get_object_by_name(compute_node.name)

        if compute_object:
            self.cluster.remove_object(compute_object) # ATTENZIONE: se non rimuove nulla fa sparire obj e basta TODO
            self.model.delete_node(compute_node)

            name_count = 1
            for container in compute_object.containers.copy():
                object_copy = copy.deepcopy(compute_object)
                object_copy.set_containers([container])
                object_copy.data["metadata"]["name"] += f"_{name_count}"

                self.cluster.add_object(object_copy)
                self.cluster.add_export_object(ExportObject(object_copy, None))

                name_count += 1

                # Refactor model
                service_node = self.model.get_node_by_name(container.fullname, Service) #TODO quì può essere none? Ocio
                compute_node = Compute(object_copy.fullname)

                self.model.add_node(compute_node)
                self.model.add_deployed_on(source_node=service_node, target_node=compute_node)

            self._add_report_row(smell, RefactoringStatus.SUCCESSFULLY_APPLIED)
            return True
        else:
            self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, compute_object_not_found_msg(compute_node.name))
            return False


