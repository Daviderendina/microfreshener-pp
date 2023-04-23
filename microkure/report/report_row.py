from microfreshener.core.analyser.smell import Smell

from microfreshenerpp.report.costants import RefactoringStatus


class ReportRow:
    pass


class RefactoringReportRow(ReportRow):

    def __init__(self, refactoring_name=None, smell: Smell = None, status: RefactoringStatus = None):
        self.refactoring_name = refactoring_name
        self.smell = smell
        self.status = status
        self.message_list = []

    def add_message(self, message: str):
        self.message_list.append(message)


