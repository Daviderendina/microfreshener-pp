from abc import abstractmethod

from microfreshener.core.analyser.smell import Smell, WobblyServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from project.kmodel.kCluster import KCluster


class Refactoring:

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        self.model = model #TODO si può togliere il model, non serve a nulla
        self.cluster = cluster

    @abstractmethod
    def apply(self, smell: Smell):
        pass


class RefactoringNotSupportedError(Exception):
    pass


class UseTimeoutRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, WobblyServiceInteractionSmell):
            raise RefactoringNotSupportedError()

        if isinstance(smell.node, Service):
            for link in smell.links_cause:

                if isinstance(link.target, Service):
                    pass # Tra Service e Service
                    # Con Istio non posso mettere direttamente il timeout tra due pod, devo mettere almeno un svc davanti al
                    # target per impostare poi il timeout per quel servizio

                if isinstance(link.target, MessageRouter):
                    pass  # 2. Tra Service e MessageRouter
                    # Faccio il deploy di un nuovo VirtualService / Destination rule per far sì che le richieste in
                    # ingresso vengano effettuate con il timeout


class AddCircuitBreakerRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
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
                    pass

                    # Devo fare il deploy di una nuova destinationRule per quel servizio (devo usare il campo host)

# DA VEDERE

## REFACTORING CHE NON RIESCO AD APPLICARE IN MANIERA AUTOMATICA
    # REFACTORING_ADD_TEAM_DATA_MANAGER, \
    # REFACTORING_SPLIT_DATABASE, \
    # REFACTORING_MERGE_SERVICES, \
    # REFACTORING_CHANGE_DATABASE_OWENRSHIP, \
    # REFACTORING_CHANGE_SERVICE_OWENRSHIP

## ? REFACTORING CHE SONO IN DUBBIO SE RIESCO A FARLI OPPURE NO
    # REFACTORING_ADD_SERVICE_DISCOVERY - DEVO PRIMA CAPIRE QUESTO SERVICE DISCOVERY COSA SIA

# REFACTORING CHE POTREI FARE IN MANIERA SEMIAUTO
    # REFACTORING_ADD_DATA_MANAGER, - in questo caso sono in grado solo di aggiungere un pod vuoto e tutta la struttura,
        # ma non ha molto senso aggiungere solo questa poca roba
    # REFACTORING_ADD_MESSAGE_BROKER, \ - in questo caso dovrebbe completamente cambiare il paradigma di comunicazione
