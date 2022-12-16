import copy

from microfreshener.core.analyser.smell import Smell, MultipleServicesInOneContainerSmell
from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute

from project.exporter.export_object import ExportObject
from project.kmodel.kube_cluster import KubeCluster
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class SplitServicesRefactoring(Refactoring):

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        super().__init__(cluster, model)

    def apply(self, smell: Smell):
        if not isinstance(smell, MultipleServicesInOneContainerSmell):
            raise RefactoringNotSupportedError

        compute_node: Compute = smell.node
        compute_object = self.cluster.get_object_by_name(compute_node.name)

        if compute_object:
            self.cluster.remove_object(compute_object)

            name_count = 1
            for container in compute_object.containers.copy():
                object_copy = copy.deepcopy(compute_object)
                object_copy.set_containers([container])
                object_copy.data["metadata"]["name"] += f"_{name_count}"

                self.cluster.add_object(object_copy)
                self.cluster.add_export_object(ExportObject(object_copy, None))

                name_count += 1

            return True
        else:
            return False

    #TODO il refactor del model non serve: è il deploy che devo dividere, il modello è già diviso!!

