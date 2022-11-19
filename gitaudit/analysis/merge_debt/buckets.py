"""Storing Contribution Information as Buckets
"""

from __future__ import annotations
from typing import List, Tuple, Dict

from pydantic import BaseModel, Field

from gitaudit.git.change_log_entry import ChangeLogEntry


class BucketEntry(BaseModel):
    """Entry for storing changes in an hierarchy branch ready for matching
    """
    merge_commit: ChangeLogEntry
    branch_commits: List[ChangeLogEntry]
    children: List[BucketEntry] = Field(default_factory=list)

    @property
    def merge_sha(self):
        """The sha that was used for merging this bucket
        (or the fast forward merge commit sha)
        """
        return self.merge_commit.sha

    @property
    def branch_shas(self):
        """Shas that come in as part for this merge commit
        """
        return list(map(lambda x: x.sha, self.branch_commits))

    @property
    def children_shas(self):
        """Shas that come in as part of this merge commit but who are themselves
        buckets with a substructure
        """
        return list(map(lambda x: x.merge_commit.sha, self.children))

    def prune_sha(self, sha: str) -> bool:
        """Prune a commit from the bucket entry

        Args:
            sha (str): The sha of the commit to be pruned

        Returns:
            bool: Indicator whether or not the bucket entry is now empty and pruning can
                be collapsed upwards the bucket entry tree
        """
        self.branch_commits = list(filter(
            lambda x: x.sha != sha,
            self.branch_commits,
        ))
        self.children = list(filter(
            lambda x: x.merge_sha != sha,
            self.children,
        ))

        if self.merge_sha == sha:
            return True

        return not self.branch_commits and not self.children

    @classmethod
    def from_change_log_entry(
        cls,
        entry: ChangeLogEntry,
        first_parent_line: List[ChangeLogEntry] = None,
    ):
        """Create Bucket from a change log entry

        Args:
            entry (ChangeLogEntry): The entry to be transformed into a bucket
            first_parent_line (List[ChangeLogEntry], optional): If this is set
                the first parent line under the entry will be regarded as an
                additional contributer to the branch commits. Defaults to None.

        Returns:
            _type_: _description_
        """
        merge_commit = entry

        branch_commits = []
        children = []

        if first_parent_line:
            assert entry.parent_shas[0] == first_parent_line[0].sha
            commit_lines = [first_parent_line] + entry.other_parents
        else:
            commit_lines = entry.other_parents

        for commit_line in commit_lines:
            for index, commit in enumerate(commit_line):
                if commit.other_parents:
                    # sub_branch_off_point
                    children.append(BucketEntry.from_change_log_entry(
                        entry=commit,
                        first_parent_line=commit_line[(index+1):],
                    ))
                    break

                # add to commits
                branch_commits.append(commit)

        return BucketEntry(
            merge_commit=merge_commit,
            branch_commits=branch_commits,
            children=children
        )

    @classmethod
    def list_from_change_log_list(cls, hier_log):
        """Given an hierarchy log create a list of BucketEntries

        Args:
            hier_log (List[ChangeLogEntry]): Hierarchy Log

        Returns:
            List[BucketEntry]: List of Bucket Entries
        """
        return [BucketEntry.from_change_log_entry(x) for x in hier_log]


def get_sha_to_bucket_entry_map(buckets: List[BucketEntry]) \
        -> Tuple[Dict[str, BucketEntry], Dict[str, ChangeLogEntry]]:
    """Generate a sha -> BucketEntry and Entry map out of a list of bucket entries

    Args:
        buckets (List[BucketEntry]): List of Bucket Entries

    Returns:
        Tuple[Dict[str, BucketEntry], Dict[str, ChangeLogEntry]]: Bucket Map, Entry Map
    """
    bucket_map = {}
    entry_map = {}

    for bucket in buckets:
        bucket_map[bucket.merge_commit.sha] = bucket
        entry_map[bucket.merge_commit.sha] = bucket.merge_commit
        for branch_commit in bucket.branch_commits:
            bucket_map[branch_commit.sha] = bucket
            entry_map[branch_commit.sha] = branch_commit

        child_bucket_map, child_entry_map = get_sha_to_bucket_entry_map(
            bucket.children)
        bucket_map.update(child_bucket_map)
        entry_map.update(child_entry_map)

    return bucket_map, entry_map


def get_linear_bucket_list(buckets: List[BucketEntry]):
    """Generate a linear list of all bucket entries

    Args:
        buckets (List[BucketEntry]): List of buckets ordered in hierarchy

    Returns:
        List[BucketEntry]: The linear list of bucket entries
    """
    bucket_list = []

    for bucket in buckets:
        bucket_list.append(bucket)
        bucket_list.extend(get_linear_bucket_list(bucket.children))

    return bucket_list


def get_merge_sha_parent_bucket_map(buckets: List[BucketEntry]):
    """Return the parent bucket for any merge commit sha

    Args:
        buckets (List[BucketEntry]): buckets in hierarchy

    Returns:
        Dict[str, BucketEntry]: Merge sha to parent bucket map
    """
    parent_map = {}

    for bucket in buckets:
        for child in bucket.children:
            parent_map[child.merge_sha] = bucket

        child_parent_map = get_merge_sha_parent_bucket_map(bucket.children)
        parent_map.update(child_parent_map)

    return parent_map


class BucketList:
    """Stores a list of bucket entries in its hierarchy
    """

    def __init__(self, hier_log) -> None:
        self.entries = BucketEntry.list_from_change_log_list(hier_log)
        self.bucket_map, self.entry_map = get_sha_to_bucket_entry_map(
            self.entries)
        self.linear_buckets = get_linear_bucket_list(self.entries)
        self.merge_sha_parent_bucket_map = get_merge_sha_parent_bucket_map(
            self.entries)
        self.merge_commit_shas = list(
            map(lambda x: x.merge_sha, self.linear_buckets))

    def prune_sha(self, sha):
        """Pune a sha from the bucket list

        Args:
            sha (str): Sha of the commit to be pruned
        """
        bucket = self.bucket_map.get(sha, None)

        if not bucket:
            return

        collapse = bucket.prune_sha(sha)

        if collapse:
            self._prune_upwards_from_bucket(bucket)

    def _prune_upwards_from_bucket(self, bucket):
        parent_bucket = self.merge_sha_parent_bucket_map.get(
            bucket.merge_sha, None)

        if parent_bucket:
            collapse = parent_bucket.prune_sha(bucket.merge_sha)
            if collapse:
                self._prune_upwards_from_bucket(parent_bucket)
        else:
            self.entries = list(
                filter(lambda x: x.merge_sha != bucket.merge_sha, self.entries))

    def prune_sha_merge_last(self, shas):
        """prunes multiples shas by pruning the branch entries before the merge commits

        Args:
            shas (List[str]): shas to be pruned from the list
        """
        merge_shas = []

        for sha in shas:
            if sha in self.merge_commit_shas:
                merge_shas.append(sha)
            else:
                self.prune_sha(sha)

        for sha in merge_shas:
            self.prune_sha(sha)
