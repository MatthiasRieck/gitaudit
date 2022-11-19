"""Reporting code for merge debt
"""

from enum import Enum

from pydantic import BaseModel

from .matchers import MatchResult


class MergeDebtReportEntrySeverity(Enum):
    """Merge Debt Severity
    """
    INFO = 1
    WARNING = 2
    ERROR = 3


class MergeDebtReportEntry(BaseModel):
    """Merge Debt Report Entry
    """
    match: MatchResult
    severity: MergeDebtReportEntrySeverity
    message: str

    @classmethod
    def info(cls, match, message):
        """Create Info Merge Debt Report Entry

        Args:
            match (MatchResult): Match Result
            message (str): Message

        Returns:
            MergeDebtReportEntry: Entry
        """
        return MergeDebtReportEntry(
            match=match,
            severity=MergeDebtReportEntrySeverity.INFO,
            message=message,
        )

    @classmethod
    def warning(cls, match, message):
        """Create Warning Merge Debt Report Entry

        Args:
            match (MatchResult): Match Result
            message (str): Message

        Returns:
            MergeDebtReportEntry: Entry
        """
        return MergeDebtReportEntry(
            match=match,
            severity=MergeDebtReportEntrySeverity.WARNING,
            message=message,
        )

    @classmethod
    def error(cls, match, message):
        """Create Error Merge Debt Report Entry

        Args:
            match (MatchResult): Match Result
            message (str): Message

        Returns:
            MergeDebtReportEntry: Entry
        """
        return MergeDebtReportEntry(
            match=match,
            severity=MergeDebtReportEntrySeverity.ERROR,
            message=message,
        )


class MergeDebtReport:  # pylint: disable=too-few-public-methods
    """Merge Debt Report
    """

    def __init__(self) -> None:
        self.entries = []

    def append_entry(self, entry: MergeDebtReportEntry):
        """Append merge debt report entry

        Args:
            entry (MergeDebtReportEntry): Merge Debt Report Entry
        """
        self.entries.append(entry)
