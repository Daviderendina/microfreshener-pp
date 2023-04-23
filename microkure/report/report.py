from microfreshener.core.analyser.smell import Smell

from microfreshenerpp.report.report_row import RefactoringReportRow, RefactoringStatus
from microfreshenerpp.report.report_exporter import RefactoringCSVReportExporter


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

    def add_row(self, refactoring_name=None, smell: Smell = None, status: RefactoringStatus = None):
        row = RefactoringReportRow(refactoring_name, smell, status)
        self.rows.append(row)
        return row


