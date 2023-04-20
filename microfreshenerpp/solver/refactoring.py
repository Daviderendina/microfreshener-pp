from abc import abstractmethod

from microfreshener.core.analyser.smell import Smell
from microfreshener.core.model import MicroToscaModel

from microfreshenerpp.exporter.export_object import ExportObject
from microfreshenerpp.ignorer.ignorer import Ignorer
from microfreshenerpp.kmodel.kube_cluster import KubeCluster
from microfreshenerpp.report.report import RefactoringReport
from microfreshenerpp.report.report_row import RefactoringStatus


class Refactoring:

    def __init__(self, cluster: KubeCluster, model: MicroToscaModel, name):
        self.cluster = cluster
        self.model = model
        self.solver_pending_ops_ref = None
        self.name = name

    @abstractmethod
    def apply(self, smell: Smell, ignorer: Ignorer) -> bool:
        pass

    def set_solver_pending_ops(self, solver_pending_ops):
        self.solver_pending_ops_ref = solver_pending_ops

    def _add_report_row(self, smell: Smell, status: RefactoringStatus, message_item):
        row = RefactoringReport().add_row(self.name, smell, status)

        if message_item:
            if isinstance(message_item, str):
                message_item = [message_item]

            for message in message_item:
                row.add_message(message)

    def _add_to_cluster(self, object) -> ExportObject:
        exp = ExportObject(object, None)
        self.cluster.add_object(object)
        self.cluster.add_export_object(exp)

        return exp


class RefactoringNotSupportedError(Exception):
    pass

