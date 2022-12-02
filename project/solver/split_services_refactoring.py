from microfreshener.core.analyser.smell import Smell
from microfreshener.core.model import MicroToscaModel
from microfreshener.core.model.nodes import Compute

from project.analyser.smell import MultipleServicesInOneContainerSmell
from project.kmodel.kCluster import KCluster
from project.kmodel.kobject_kind import KObjectKind
from project.solver.refactoring import RefactoringNotSupportedError, Refactoring


class SplitServicesRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        import copy

        if not isinstance(smell, MultipleServicesInOneContainerSmell):
            raise RefactoringNotSupportedError

        compute_node: Compute = smell.node
        compute_object = self.cluster.get_object_by_name(compute_node.name)

        if compute_object:
            self.cluster.remove_object(compute_object, KObjectKind.get_from_class(compute_object.__class__))

            name_count = 1
            for container in compute_object.get_containers().copy():
                object_copy = copy.deepcopy(compute_object)
                object_copy.set_containers([container])
                object_copy.metadata.name += f"_{name_count}"

                self.cluster.add_object(object_copy, KObjectKind.get_from_class(object_copy.__class__))

                name_count += 1
            pass


        #TODO devo fare in questo caso anche il refactoring del MicroToscaModel!! Questo deve ovviamente essere fatto prima di arrivare qui

        #TODO devo ovviamente esportare anche i nuovi files