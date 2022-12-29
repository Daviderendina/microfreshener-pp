from enum import Enum

from microfreshener.core.analyser.smell import Smell, NodeSmell, GroupSmell


class RefactoringStatus(Enum):
    SUCCESSFULLY_APPLIED = "SUCCESSFULLY_APPLIED",  # "Refactoring performed correctly",
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED",  # "Actions required to finish refactoring application",
    NOT_APPLIED = "NOT_APPLIED"  # "Refactoring not applied"


class ReportRow:
    pass


class RefactoringReportRow(ReportRow):

    def __init__(self, refactoring_name = None, smell: Smell = None, status: RefactoringStatus = None):
        self.refactoring_name = refactoring_name
        self.smell = smell
        self.status = status
        self.message_list = []

    def add_message(self, message: str):
        self.message_list.append(message)


