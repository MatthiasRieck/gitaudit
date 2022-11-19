"""Matchers for merge debt analysis
"""

from enum import Enum
from typing import List
from hashlib import sha1

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


def numstat_to_sha1(entry: ChangeLogEntry, with_additions_deletions=True):
    """Calculates a sha1 hash out of the numstat file changes

    Args:
        entry (ChangeLogEntry): Change Log Entry
        with_additions_deletions (bool, optional): Whether additions and deletions shall be
            accounted for. Defaults to True.

    Returns:
        str: sha1 hash
    """
    if with_additions_deletions:
        file_add_del_texts = map(
            lambda x: f"{x.path}({x.additions}|{x.deletions})", entry.sorted_numstat)
    else:
        file_add_del_texts = map(lambda x: x.path, entry.sorted_numstat)
    return sha1("".join(file_add_del_texts).encode('utf-8')).hexdigest()


def create_numstat_map(entries: List[ChangeLogEntry], with_additions_deletions: bool = True):
    """Creates a numstat sha1 to change log entry map that can be used for commit matching

    Args:
        entries (List[ChangeLogEntry]): List of change log entries
        with_additions_deletions (bool, optional): Whether additions / deletions shall be accounted
            for in the map generation. Defaults to True.

    Returns:
        Dict[str, ChangeLogEntry]: Numstat sha1 to ChangeLogEntry map
    """
    numstat_map = {}
    ignore_entries = []

    for entry in entries:
        if not entry.numstat:
            continue

        stat_sha1 = numstat_to_sha1(entry, with_additions_deletions)

        if stat_sha1 in ignore_entries:
            continue

        if stat_sha1 in numstat_map:
            numstat_map.pop(stat_sha1)
            ignore_entries.append(stat_sha1)
            continue

        numstat_map[stat_sha1] = entry

    return numstat_map


class FilesChangedMatcher(Matcher):  # pylint: disable=too-few-public-methods
    """In case a cherry pick was NOT done with the -x option enabled an exact matching is not
    possible. But if a cherry pick was done successfully, the files changed in both commits shall
    be the exact same. Therefore, the changes files withing a commit can be used to determine
    if two commits are equal.

    All matches will have a STRONG confidence level. If there are multiple matches the additions and
    deletions will be used to filter false positives (note that additions and deletions check is
    done for all matches automatically to proove confidence). In case the additions and deletions
    are not matched the confidence level is dropped to LOW.
    """

    def __init__(self, with_additions_deletions=True) -> None:
        super().__init__()
        self.with_additions_deletions = with_additions_deletions

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

        numstat_head_map = create_numstat_map(
            list(entry_head_map.values()),
            self.with_additions_deletions,
        )
        numstat_base_map = create_numstat_map(
            list(entry_base_map.values()),
            self.with_additions_deletions,
        )

        matches = []

        confidence = MatchConfidence.STRONG \
            if self.with_additions_deletions else MatchConfidence.GOOD

        for cp_sha, head_entry in numstat_head_map.items():
            if cp_sha not in numstat_base_map:
                continue

            matches.append(MatchResult(
                head=head_entry,
                base=numstat_base_map[cp_sha],
                confidence=confidence,
            ))

        return matches


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
