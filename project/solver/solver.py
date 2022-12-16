from abc import abstractmethod

from microfreshener.core.analyser.costants import REFACTORING_ADD_MESSAGE_ROUTER, \
    SMELL_ENDPOINT_BASED_SERVICE_INTERACTION, SMELL_WOBBLY_SERVICE_INTERACTION_SMELL, \
    SMELL_NO_API_GATEWAY, SMELL_MULTIPLE_SERVICES_IN_ONE_CONTAINER, REFACTORING_SPLIT_SERVICES, \
    REFACTORING_ADD_API_GATEWAY, REFACTORING_USE_TIMEOUT, REFACTORING_ADD_CIRCUIT_BREAKER, REFACTORING_NAMES
from microfreshener.core.analyser.smell import Smell
from typing import List

from project.kmodel.kube_cluster import KubeCluster
from project.kmodel.kube_object import KubeObject
from project.solver.refactoringimpl.add_API_gateway_refactoring import AddAPIGatewayRefactoring
from project.solver.refactoringimpl.add_circuit_breaker_refactoring import AddCircuitBreakerRefactoring
from project.solver.refactoringimpl.add_message_router_refactoring import AddMessageRouterRefactoring
from project.solver.pending_ops import PENDING_OPS
from project.solver.refactoringimpl.split_services_refactoring import SplitServicesRefactoring
from project.solver.refactoringimpl.use_timeout_refactoring import UseTimeoutRefactoring


class Solver:

    @abstractmethod
    def solve(self, smells: list[Smell]) -> KubeCluster:
        pass


class KubeSolver(Solver):

    def __init__(self, kube_cluster: KubeCluster, refactoring_list: List[str] = None):
        self.kube_cluster = kube_cluster
        self.pending_ops: (PENDING_OPS, KubeObject) = []

        self.refactoring = {}
        for refactoring in refactoring_list:
            if refactoring not in REFACTORING_NAMES:
                raise ValueError(f"Refactoring passed ({refactoring}) is not a defined name! ")

        if refactoring_list is None:
            refactoring_list = REFACTORING_NAMES

        self.set_refactoring(refactoring_list)


    def solve(self, smells: list[Smell]) -> KubeCluster:
        for smell in smells:
            refactoring: list = self.refactoring.get(smell.name, None)
            if refactoring is not None:
                i = 0
                refactoring_res = False
                while i < len(refactoring) and not refactoring_res:
                    refactoring_res = refactoring[i].apply(smell)
                    i += 1

        for ops, obj in self.pending_ops:
            x = ops.value

        return self.kube_cluster

    def set_refactoring(self, refactoring_list):
        refactoring_list = list(set(refactoring_list))

        if REFACTORING_ADD_MESSAGE_ROUTER in refactoring_list:
            self.refactoring[SMELL_ENDPOINT_BASED_SERVICE_INTERACTION] = [AddMessageRouterRefactoring(self.kube_cluster)]

        if REFACTORING_USE_TIMEOUT in refactoring_list:
            self.refactoring[SMELL_WOBBLY_SERVICE_INTERACTION_SMELL] = [UseTimeoutRefactoring(self.kube_cluster)]

        if REFACTORING_ADD_CIRCUIT_BREAKER in refactoring_list:
            if SMELL_WOBBLY_SERVICE_INTERACTION_SMELL not in self.refactoring.keys():
                self.refactoring[SMELL_WOBBLY_SERVICE_INTERACTION_SMELL] += [AddCircuitBreakerRefactoring(self.kube_cluster)]

        if REFACTORING_ADD_API_GATEWAY in refactoring_list:
            refactoring = AddAPIGatewayRefactoring(self.kube_cluster)
            refactoring.set_solver_pending_ops(self.pending_ops)
            self.refactoring[SMELL_NO_API_GATEWAY] = [refactoring]

        if REFACTORING_SPLIT_SERVICES in refactoring_list:
            self.refactoring[SMELL_MULTIPLE_SERVICES_IN_ONE_CONTAINER] = [SplitServicesRefactoring(self.kube_cluster)]

