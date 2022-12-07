from microfreshener.core.analyser.smell import WobblyServiceInteractionSmell, Smell
from microfreshener.core.model import MicroToscaModel, Service, MessageRouter

from k8s_template.kobject_generators import generate_timeout_virtualsvc_for_svc
from project.kmodel.kCluster import KCluster
from project.kmodel.kService import KService
from project.kmodel.kobject_kind import KObjectKind
from project.solver.refactoring import Refactoring, RefactoringNotSupportedError


class UseTimeoutRefactoring(Refactoring):

    DEFAULT_TIMEOUT_SEC = 2

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
                    # target per impostare poi il timeout per quel servizio - SICURAMENTE QUESTO E' MEGLIO ESEGUIRLO PER ULTIMO,
                    # COSÌ DA AGGIUNGERE TUTTI I SVC MANCANTI!! QUESTO CASO IN TEORIA COSÌ NON ESISTE (O QUASI) #TODO

                if isinstance(link.target, MessageRouter):
                    k_service: KService = self.cluster.get_object_by_name(link.target.name)
                    virtual_service = generate_timeout_virtualsvc_for_svc(k_service, self.DEFAULT_TIMEOUT_SEC)

                    self.cluster.add_object(virtual_service, KObjectKind.ISTIO_VIRTUAL_SERVICE)

                    #TODO in verità in questo modo viene aggiunto il timeout per tutte le connessioni in ingresso: questo va bene?

                #TODO devo assicurarmi che non ci siano già VService definiti? Potrei vedere se ci sono VService che hanno
                # l'host come destinazione e capire in base agli hosts cosa fare. Se però funziona così è meglio