from enum import Enum


class RefactoringStatus(Enum):
    SUCCESSFULLY_APPLIED = "SUCCESSFULLY_APPLIED",  # "Refactoring performed correctly",
    PARTIALLY_APPLIED = "PARTIALLY_APPLIED",  # "Actions required to finish refactoring application",
    NOT_APPLIED = "NOT_APPLIED"  # "Refactoring not applied"