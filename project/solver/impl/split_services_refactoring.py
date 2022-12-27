import copy

from microfreshener.core.analyser.costants import REFACTORING_SPLIT_SERVICES
from microfreshener.core.analyser.smell import Smell, MultipleServicesInOneContainerSmell
from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute, Service

from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.report.report_msg import compute_object_not_found_msg, cannot_refactor_model_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class SplitServicesRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_SPLIT_SERVICES)

    def apply(self, smell: Smell):
        object_to_add = []
        export_object_to_add = []
        abort = False

        if not isinstance(smell, MultipleServicesInOneContainerSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        compute_node: Compute = smell.node
        workload = self.cluster.get_object_by_name(compute_node.name)

        if workload:
            name_count = 1
            for container in workload.containers.copy():

                object_copy = copy.deepcopy(workload)
                object_copy.set_containers([container])
                object_copy.data["metadata"]["name"] += f"_{name_count}"

                if self._refactor_model(container, object_copy):
                    object_to_add.append(object_copy)
                    export_object_to_add.append(ExportObject(object_copy, None))
                else:
                    abort = True

                name_count += 1

            if not abort:
                self.cluster.remove_object(workload)
                self.model.delete_node(compute_node)
                for object in object_to_add:
                    self.cluster.add_object(object)
                for exp_object in export_object_to_add:
                    self.cluster.add_export_object(exp_object)

                self._add_report_row(smell, RefactoringStatus.SUCCESSFULLY_APPLIED)
                return True
            else:
                self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, cannot_refactor_model_msg())
                return False
        else:
            self._add_report_row(smell, RefactoringStatus.NOT_APPLIED, compute_object_not_found_msg(compute_node.name))
            return False

    def _refactor_model(self, container, object_copy):
        # Refactor model
        service_node = self.model.get_node_by_name(container.typed_fullname)
        if service_node:
            compute_node = Compute(object_copy.typed_fullname)

            self.model.add_node(compute_node)
            self.model.add_deployed_on(source_node=service_node, target_node=compute_node)
            return True

        return False