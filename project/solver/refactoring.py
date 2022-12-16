from abc import abstractmethod

from microfreshener.core.analyser.smell import Smell
from microfreshener.core.model import MicroToscaModel

from project.kmodel.kube_cluster import KubeCluster


class Refactoring:

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel):
        self.cluster = cluster
        self.model = model
        self.solver_pending_ops = None

    @abstractmethod
    def apply(self, smell: Smell) -> bool:
        pass

    def set_solver_pending_ops(self, solver_pending_ops):
        self.solver_pending_ops = solver_pending_ops


class RefactoringNotSupportedError(Exception):
    pass



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
