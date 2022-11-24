from abc import abstractmethod

from microfreshener.core.analyser.smell import Smell, NoApiGatewaySmell, WobblyServiceInteractionSmell, \
    EndpointBasedServiceInteractionSmell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from project.analyser.smell import MultipleServicesInOneContainerSmell
from project.kmodel.kCluster import KCluster


class Refactoring:

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        self.model = model
        self.cluster = cluster

    @abstractmethod
    def apply(self, smell: Smell):
        pass


class RefactoringNotSupportedError(Exception):
    pass


class AddAPIGatewayRefactoring(Refactoring):
    # https://alesnosek.com/blog/2017/02/14/accessing-kubernetes-pods-from-outside-of-the-cluster/
    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, NoApiGatewaySmell):
            raise RefactoringNotSupportedError


class SplitServicesRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, MultipleServicesInOneContainerSmell):
            raise RefactoringNotSupportedError

        # compute_node = smell.node

        # kobject = trovo l'oggetto che definisce quei due pod

        # for service_node in compute_node.incoming_interactions:

            # Devo fare una copia del kobject

            # Togliere uno dei due container

            # Cambiare il nomde dell'oggetto (posso semplicemente aggiungere '-1' oppure '-2' a cosa già c'è, anche per le label mi conviene fare lo stesso)

            # Prendo il servizio che espone il pod e aggiungo solo una porta (siamo sicuri?)

        pass

        #TODO devo fare in questo caso anche il refactoring del MicroToscaModel!! Questo deve ovviamente essere fatto prima di arrivare qui


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


class AddMessageRouterRefactoring(Refactoring):

    def __init__(self, model: MicroToscaModel, cluster: KCluster):
        super().__init__(model, cluster)

    def apply(self, smell: Smell):
        if not isinstance(smell, EndpointBasedServiceInteractionSmell):
            raise RefactoringNotSupportedError

        if isinstance(smell.node, Service):
            for link in [l for l in smell.links_cause if isinstance(l.target, Service)]:
                pass

                # Prendo il nodo corrispondente al service l.target

                # Devo fare un (Kube) Service che esponga il Pod corrispondente

                # Lo sviluppatore deve in qualche modo confermare di aver cambiato le chiamate, dall'IP al nome del svc
                # (il nome lo prendo direttamente dal pod/deploy/etc..)


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
