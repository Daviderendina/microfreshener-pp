from enum import Enum

from microfreshener.core.analyser.smell import Smell, NodeSmell, GroupSmell


class RefactoringStatus(Enum):
    SUCCESSFULLY_APPLIED = "SUCCESSFULLY_APPLIED",  # "Refactoring performed correctly",
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED",  # "Actions required to finish refactoring application",
    NOT_APPLIED = "NOT_APPLIED"  # "Refactoring not applied"


class ReportRow:
    pass


class RefactoringReportRow(ReportRow):

    def __init__(self, refactoring_name, smell: Smell, status: RefactoringStatus, message: str):
        self.refactoring_name = refactoring_name
        self.smell = smell
        self.status = status
        self.message = message



