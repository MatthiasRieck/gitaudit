"""Reporting code for merge debt
"""

from enum import Enum
from typing import List

from pydantic import BaseModel

from gitaudit.git.change_log_entry import ChangeLogEntry
from .matchers import MatchResult


class MergeDebtReportAlertSeverity(Enum):
    """Merge Debt Severity
    """
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class MergeDebtAlert(BaseModel):
    """Merge Debt Report Alert
    """
    match: MatchResult
    severity: MergeDebtReportAlertSeverity
    message: str

    @classmethod
    def info(cls, match, message):
        """Create Info Merge Debt Report Alert

        Args:
            match (MatchResult): Match Result
            message (str): Message

        Returns:
            MergeDebtAlert: Alert
        """
        return MergeDebtAlert(
            match=match,
            severity=MergeDebtReportAlertSeverity.INFO,
            message=message,
        )

    @classmethod
    def warning(cls, match, message):
        """Create Warning Merge Debt Report Alert

        Args:
            match (MatchResult): Match Result
            message (str): Message

        Returns:
            MergeDebtAlert: Alert
        """
        return MergeDebtAlert(
            match=match,
            severity=MergeDebtReportAlertSeverity.WARNING,
            message=message,
        )

    @classmethod
    def error(cls, match, message):
        """Create Error Merge Debt Report Alert

        Args:
            match (MatchResult): Match Result
            message (str): Message

        Returns:
            MergeDebtAlert: Alert
        """
        return MergeDebtAlert(
            match=match,
            severity=MergeDebtReportAlertSeverity.ERROR,
            message=message,
        )


class MergeDebtReport:
    """Merge Debt Report
    """

    def __init__(self) -> None:
        self.alerts = []
        self.matches = []
        self.base_prunes = []
        self.head_prunes = []
        self.base_unmatched = []
        self.head_unmatched = []

    def append_alert(self, alert: MergeDebtAlert):
        """Append merge debt report alert

        Args:
            alert (MergeDebtReportEntry): Merge Debt Report Alert
        """
        self.alerts.append(alert)

    def append_match(self, match: MatchResult):
        """Appends merge debt match entry

        Args:
            match (MatchResult): Merge Debt Match Entry
        """
        self.matches.append(match)

    def append_head_prune(self, entry: ChangeLogEntry):
        """Append a head prune entry

        Args:
            entry (ChangeLogEntry): Pruned change log entry
        """
        self.head_prunes.append(entry)

    def append_base_prune(self, entry: ChangeLogEntry):
        """Append a base prune entry

        Args:
            entry (ChangeLogEntry): Pruned change log entry
        """
        self.base_prunes.append(entry)

    def dict(self, head_entries: List[ChangeLogEntry], base_entries: List[ChangeLogEntry]) -> dict:
        """Creates Report Entry

        Args:
            head_entries (List[ChangeLogEntry]): Unmatched head entries
            base_entries (List[ChangeLogEntry]): Unmatched base entries

        Returns:
            dict: report dictionary
        """
        self.base_unmatched = base_entries
        self.head_unmatched = head_entries

        return {
            "unmatched": {
                "head_entries": list(map(
                    lambda x: x.dict(),
                    head_entries,
                )),
                "base_entries": list(map(
                    lambda x: x.dict(),
                    base_entries,
                )),
            },
            "pruned": {
                "head_entries": list(map(
                    lambda x: x.dict(),
                    self.head_prunes,
                )),
                "base_entries": list(map(
                    lambda x: x.dict(),
                    self.base_prunes,
                )),
            },
            "matches": list(map(
                lambda x: x.dict(),
                self.matches,
            )),
            "alerts": list(map(
                lambda x: x.dict(),
                self.alerts,
            )),
        }
