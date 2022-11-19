"""Matchers for merge debt analysis
"""

from enum import Enum
from typing import List

from pydantic import BaseModel

from gitaudit.git.change_log_entry import ChangeLogEntry
from .buckets import BucketEntry, get_sha_to_bucket_entry_map


class MatchConfidence(Enum):
    """Enumeration for showing Match Confidence
    """
    ABSOLUTE = 1
    STRONG = 2
    GOOD = 3
    LOW = 4


class MatchResult(BaseModel):
    """Match Result consisting of head, base, and confidence entries
    """
    head: ChangeLogEntry
    base: ChangeLogEntry
    confidence: MatchConfidence


class Matcher:  # pylint: disable=too-few-public-methods
    """Generic class for matching commits
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """
        raise NotImplementedError


class SameCommitMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """Accounts for branching strategies where dev and master branches are regularly cross merged.

    In very rare occasions it can happen that a feature branch was created before branch off
    and then can be merged into both branches that are to be matched with different merge commits.

    All matches will have an ABSOLUTE confidence level.
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Returns:
            List[MatchResult]: List of commit Matches
        """
        _, entry_head_map = get_sha_to_bucket_entry_map(head)
        _, entry_base_map = get_sha_to_bucket_entry_map(base)

        matches = []

        for sha, head_entry in entry_head_map.items():
            if sha in entry_base_map:
                matches.append(MatchResult(
                    head=head_entry,
                    base=entry_base_map[sha],
                    confidence=MatchConfidence.ABSOLUTE,
                ))

        return matches


class DirectCherryPickMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """If a cherry pick was done with the -x option the commit message will have a
    (cherry picked from commit <sha>) message in the commit body. This sha can be used for matching.

    The cherry pick matcher will match in both directions (head <-> base) as it can happen that in a
    project the bugfix has to be done quickly in release and is then cherry picked to main later.

    All matches will have an ABSOLUTE confidence level.
    """

    def __init__(self, head_to_base: bool = True, base_to_head: bool = True) -> None:
        """Constructor

        Args:
            head_to_base (bool): Head commit was cherry picked with -x from base
            base_to_head (bool): Base commit was cherry picked with -x from head
        """
        super().__init__()

        self.head_to_base = head_to_base
        self.base_to_head = base_to_head

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """

        _, entry_head_map = get_sha_to_bucket_entry_map(head)
        _, entry_base_map = get_sha_to_bucket_entry_map(base)

        matches = []

        if self.head_to_base:
            for head_entry in entry_head_map.values():
                if not head_entry.cherry_pick_sha:
                    continue

                if head_entry.cherry_pick_sha in entry_base_map:
                    matches.append(MatchResult(
                        head=head_entry,
                        base=entry_base_map[head_entry.cherry_pick_sha],
                        confidence=MatchConfidence.ABSOLUTE,
                    ))

        if self.base_to_head:
            for base_entry in entry_base_map.values():
                if not base_entry.cherry_pick_sha:
                    continue

                if base_entry.cherry_pick_sha in entry_head_map:
                    matches.append(MatchResult(
                        head=entry_head_map[base_entry.cherry_pick_sha],
                        base=base_entry,
                        confidence=MatchConfidence.ABSOLUTE,
                    ))

        return matches


class ThirdPartyCherryPickMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """It can happen that a bug fix was created on master and then is cherry picked with -x option
    to release and hotfix branch. If a matching between release and hotfix is made the sha in the
    commit messase (cherry picked from commit <sha>) will point to a third party commit unrelated
    to the branches under comparison.

    All matches will have an ABSOLUTE confidence level.
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """

        _, entry_head_map = get_sha_to_bucket_entry_map(head)
        _, entry_base_map = get_sha_to_bucket_entry_map(base)

        matches = []

        cherry_picked_from_head_map = {x.cherry_pick_sha: x for x in filter(
            lambda entry: entry.cherry_pick_sha, entry_head_map.values())}
        cherry_picked_from_base_map = {x.cherry_pick_sha: x for x in filter(
            lambda entry: entry.cherry_pick_sha, entry_base_map.values())}

        for cp_sha, head_entry in cherry_picked_from_head_map.items():
            if cp_sha not in cherry_picked_from_base_map:
                continue

            matches.append(MatchResult(
                head=head_entry,
                base=cherry_picked_from_base_map[cp_sha],
                confidence=MatchConfidence.ABSOLUTE,
            ))

        return matches


class ChangedFilesMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """In case a cherry pick was NOT done with the -x option enabled an exact matching is not
    possible. But if a cherry pick was done successfully, the files changed in both commits shall
    be the exact same. Therefore, the changes files withing a commit can be used to determine
    if two commits are equal.

    All matches will have a STRONG confidence level. If there are multiple matches the additions and
    deletions will be used to filter false positives (note that additions and deletions check is
    done for all matches automatically to proove confidence). In case the additions and deletions
    are not matched the confidence level is dropped to LOW.
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """


class WhitelistMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """A whitelist can be provided from an outside data source to match head and base commits.

    All matches will have an ABSOLUTE confidene level.
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """


class JiraIssueKeyMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """Based on the regular expression r'[\\w\\d]+-\\d+' which matches jira issue keys possible
    matches are determined. A custom regular expression can also be provided.
    A commit may contain multiple issue keys, also multiple matches are possible.

    All matches will have a GOOD confidence level. In case the additions and deletions
    are not matched the confidence level is dropped to LOW.
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """


class SubjectMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """Based on the subject it is checked whether head subject is contained in base or vice versa.

    All matches will have a GOOD confidence level. In case the additions and deletions
    are not matched the confidence level is dropped to LOW.
    """

    def match(self, head: List[BucketEntry], base: List[BucketEntry]) -> List[MatchResult]:
        """Match the bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            List[MatchResult]: List of commit Matches
        """
