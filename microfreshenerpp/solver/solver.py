from abc import abstractmethod

from microfreshener.core.analyser.costants import REFACTORING_ADD_MESSAGE_ROUTER, \
    SMELL_ENDPOINT_BASED_SERVICE_INTERACTION, SMELL_WOBBLY_SERVICE_INTERACTION_SMELL, \
    SMELL_NO_API_GATEWAY, SMELL_MULTIPLE_SERVICES_IN_ONE_CONTAINER, REFACTORING_SPLIT_SERVICES, \
    REFACTORING_ADD_API_GATEWAY, REFACTORING_USE_TIMEOUT, REFACTORING_ADD_CIRCUIT_BREAKER, REFACTORING_NAMES
from typing import List

from microfreshener.core.analyser.smell import Smell, NodeSmell, GroupSmell
from microfreshener.core.model import MicroToscaModel

from microfreshenerpp.ignorer.impl.ignore_config import IgnoreConfig, IgnoreType
from microfreshenerpp.ignorer.impl.ignore_nothing import IgnoreNothing
from microfreshenerpp.kmodel.kube_cluster import KubeCluster
from microfreshenerpp.kmodel.kube_object import KubeObject
from microfreshenerpp.solver.impl.add_API_gateway_refactoring import AddAPIGatewayRefactoring
from microfreshenerpp.solver.impl.add_circuit_breaker_refactoring import AddCircuitBreakerRefactoring
from microfreshenerpp.solver.impl.add_message_router_refactoring import AddMessageRouterRefactoring
from microfreshenerpp.solver.pending_ops import PENDING_OPS
from microfreshenerpp.solver.impl.split_services_refactoring import SplitServicesRefactoring
from microfreshenerpp.solver.impl.use_timeout_refactoring import UseTimeoutRefactoring


class Solver:

    @abstractmethod
    def solve(self, smells) -> KubeCluster:
        pass


class KubeSolver(Solver):

    def __init__(self, kube_cluster: KubeCluster, model: MicroToscaModel, refactoring_list: List[str],
                 ignore: IgnoreConfig = IgnoreNothing()):
        self.kube_cluster = kube_cluster
        self.model = model
        self.pending_ops: (PENDING_OPS, KubeObject) = []
        self.ignore = ignore

        self.refactoring = {}
        if refactoring_list is None:
            refactoring_list = REFACTORING_NAMES

        for refactoring in refactoring_list:
            if refactoring not in REFACTORING_NAMES:
                raise ValueError(f"Refactoring passed ({refactoring}) is not a defined name! ")

        self.set_refactoring(refactoring_list)

    def apply_refactoring(self, refactoring_list, smell, ignorer):
        i = 0
        refactoring_res = False
        while i < len(refactoring_list) and not refactoring_res:
            refactoring_res = refactoring_list[i].apply(smell, ignorer)
            i += 1
        return refactoring_res

    def solve(self, smells, ignorer=IgnoreNothing()):
        smell_solved = 0
        for smell in [s for s in smells if s]:
            available_refactoring = self.get_available_refactoring(smell)

            if available_refactoring:
                result = self.apply_refactoring(available_refactoring, smell, ignorer)
                if result:
                    smell_solved += 1

        for pending_operation, obj in self.pending_ops:
            pending_operation(obj)

        return smell_solved

    def get_available_refactoring(self, smell: Smell):
        available_refactoring: list = self.refactoring.get(smell.name, [])

        for refactoring in available_refactoring:
            if isinstance(smell, NodeSmell):
                if self.ignore.is_ignored(smell.node, IgnoreType.REFACTORING, refactoring.name):
                    available_refactoring.remove(refactoring)

            elif isinstance(smell, GroupSmell):
                for node in smell.group.members:
                    if self.ignore.is_ignored(node, IgnoreType.REFACTORING, smell.name):
                        available_refactoring.remove(refactoring)

        return available_refactoring

    def set_refactoring(self, refactoring_list):
        refactoring_list = list(set(refactoring_list))

        if REFACTORING_ADD_MESSAGE_ROUTER in refactoring_list:
            self.refactoring[SMELL_ENDPOINT_BASED_SERVICE_INTERACTION] = [AddMessageRouterRefactoring(self.kube_cluster, self.model)]

        if REFACTORING_USE_TIMEOUT in refactoring_list:
            self.refactoring[SMELL_WOBBLY_SERVICE_INTERACTION_SMELL] = [UseTimeoutRefactoring(self.kube_cluster, self.model)]

        if REFACTORING_ADD_CIRCUIT_BREAKER in refactoring_list:
            if SMELL_WOBBLY_SERVICE_INTERACTION_SMELL in self.refactoring.keys():
                self.refactoring[SMELL_WOBBLY_SERVICE_INTERACTION_SMELL] += [AddCircuitBreakerRefactoring(self.kube_cluster, self.model)]
            else:
                self.refactoring[SMELL_WOBBLY_SERVICE_INTERACTION_SMELL] = [AddCircuitBreakerRefactoring(self.kube_cluster, self.model)]

        if REFACTORING_ADD_API_GATEWAY in refactoring_list:
            refactoring = AddAPIGatewayRefactoring(self.kube_cluster, self.model)
            refactoring.set_solver_pending_ops(self.pending_ops)
            self.refactoring[SMELL_NO_API_GATEWAY] = [refactoring]

        if REFACTORING_SPLIT_SERVICES in refactoring_list:
            self.refactoring[SMELL_MULTIPLE_SERVICES_IN_ONE_CONTAINER] = [SplitServicesRefactoring(self.kube_cluster, self.model)]

