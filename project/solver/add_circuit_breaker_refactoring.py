from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell, Smell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_circuit_breaker_for_svc
from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_networking import KubeService
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError


class AddCircuitBreakerRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KubeCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, WobblyServiceInteractionSmell):
            raise RefactoringNotSupportedError

        if isinstance(smell.node, Service):
            for link in smell.links_cause:

                if isinstance(link.target, Service):
                    # In questo caso con Istio non saprei come fare senza mettere un servizio davanti. #TODO dovrei provare Istio
                    pass

                if isinstance(link.target, MessageRouter):
                    kube_service = self.cluster.get_object_by_name(link.target.name)

                    if not isinstance(kube_service, KubeService):
                        return

                    circuit_breaker = generate_circuit_breaker_for_svc(kube_service)
                    self.cluster.add_object(circuit_breaker)