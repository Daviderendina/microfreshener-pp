from microfreshener.core.analyser.smell import Smell

from project.report.report_row import RefactoringReportRow, RefactoringStatus
from project.report.report_exporter import RefactoringCSVReportExporter


class Report(object):
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance.rows = []
            cls.__instance.exporter = RefactoringCSVReportExporter()

        return cls.__instance

    def export(self):
        self.exporter.export(self)


class RefactoringReport(Report):

    def add_row(self, refactoring_name, smell: Smell, status: RefactoringStatus, message: str):
        self.rows.append(RefactoringReportRow(refactoring_name, smell, status, message))

