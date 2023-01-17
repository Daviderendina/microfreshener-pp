import copy

from microfreshener.core.analyser.costants import REFACTORING_SPLIT_SERVICES
from microfreshener.core.analyser.smell import Smell, MultipleServicesInOneContainerSmell
from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute, Service

from project.exporter.export_object import ExportObject
from project.ignorer.ignorer import IgnoreType
from project.ignorer.impl.ignore_nothing import IgnoreNothing
from project.kmodel.kube_cluster import KubeCluster
from project.report.report import RefactoringReport
from project.report.report_msg import compute_object_not_found_msg, cannot_refactor_model_msg, created_resource_msg, \
    resource_deleted_msg
from project.report.report_row import RefactoringStatus
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class SplitServicesRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model, REFACTORING_SPLIT_SERVICES)

    def apply(self, smell: Smell, ignorer=IgnoreNothing()):
        object_to_add = []
        export_object_to_add = []
        abort = False

        if not isinstance(smell, MultipleServicesInOneContainerSmell):
            raise RefactoringNotSupportedError(f"Refactoring {self.name} not supported for smell {smell.name}")

        if ignorer.is_ignored(smell.node, IgnoreType.REFACTORING, self.name):
            return False

        report_row = RefactoringReport().add_row(smell=smell, refactoring_name=self.name)

        compute_node: Compute = smell.node
        workload = self.cluster.get_object_by_name(compute_node.name)

        if workload:
            for container in workload.containers.copy():
                object_copy = copy.deepcopy(workload)
                object_copy.set_containers([container])
                object_copy.data["metadata"]["name"] = f"{container.name}-{object_copy.data['metadata']['name']}"

                if self._refactor_model(container, object_copy):
                    exp = ExportObject(object_copy, None)
                    object_to_add.append(object_copy)
                    export_object_to_add.append(exp)

                    report_row.add_message(created_resource_msg(object_copy, exp.out_fullname))
                else:
                    report_row.message_list = []
                    abort = True

            if not abort:
                self.cluster.remove_object(workload)
                self.model.delete_node(compute_node)

                #TODO the deletion of the relationshipps doesn't work, so i have to do manually for the moment
                for dep in compute_node.deploys.copy():
                    dep.source.remove_deployed_on(dep)

                report_row.add_message(resource_deleted_msg(workload))

                for object in object_to_add:
                    self.cluster.add_object(object)
                for exp_object in export_object_to_add:
                    self.cluster.add_export_object(exp_object)

                report_row.status = RefactoringStatus.SUCCESSFULLY_APPLIED
                return True
            else:
                report_row.add_message(cannot_refactor_model_msg())
                report_row.status = RefactoringStatus.NOT_APPLIED
                return False
        else:
            report_row.add_message(compute_object_not_found_msg(compute_node.name))
            report_row.status = RefactoringStatus.NOT_APPLIED
            return False

    def _refactor_model(self, container, object_copy):
        service_node = self.model.get_node_by_name(container.typed_fullname)

        if service_node:
            compute_node = Compute(object_copy.typed_fullname)

            self.model.add_node(compute_node)
            self.model.add_deployed_on(source_node=service_node, target_node=compute_node)

            return True

        return False
