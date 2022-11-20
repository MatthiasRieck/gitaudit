"""Code for Pruning
"""
from typing import List, Tuple
from enum import Enum
from itertools import compress
import re

from gitaudit.git.change_log_entry import ChangeLogEntry
from .buckets import BucketEntry, get_sha_to_bucket_entry_map


class PruneBehavior(Enum):
    """Select desired pruning behavior
    """
    INDIVIDUAL = 1
    BUCKET_IF_ALL = 2
    BUCKET_IF_ANY = 3


class Pruner:  # pylint: disable=too-few-public-methods
    """Generic class for pruning commits without matching
    """

    def __init__(
        self,
        prune_head: bool = True,
        prune_base: bool = True,
        behavior: PruneBehavior = PruneBehavior.BUCKET_IF_ALL,
    ) -> None:
        self.prune_head = prune_head
        self.prune_base = prune_base
        self.behavior = behavior

    def prune(self, head: List[BucketEntry], base: List[BucketEntry]) \
            -> Tuple[List[ChangeLogEntry], List[ChangeLogEntry]]:
        """Prune bucket entries

        Args:
            head (List[BucketEntry]): Head Bucket List
            base (List[BucketEntry]): Base Bucket List

        Raises:
            NotImplementedError: Abstract Placeholder

        Returns:
            Tuple[List[PruneResult], List[PruneResult]]: List of head, base commits
                to be pruned
        """
        head_prune_results = []
        base_prune_results = []

        if self.prune_head:
            head_prune_results = self._prune_list(head)
        if self.prune_base:
            base_prune_results = self._prune_list(base)

        return head_prune_results, base_prune_results

    def _prune_list(self, bucket_list):
        prune_results = []
        for bucket in bucket_list:
            _, entry_map = get_sha_to_bucket_entry_map([bucket])
            do_prune_map = {}

            for sha, entry in entry_map.items():
                do_prune_map[sha] = self._do_prune_entry(entry)

            if self.behavior == PruneBehavior.BUCKET_IF_ALL:
                prune_entries = list(entry_map.values()) if all(
                    entry_map.values()) else []
            elif self.behavior == PruneBehavior.BUCKET_IF_ANY:
                prune_entries = list(entry_map.values()) if any(
                    entry_map.values()) else []
            else:
                prune_shas = list(
                    compress(do_prune_map.keys(), do_prune_map.values()))
                prune_entries = [entry_map[x] for x in prune_shas]

            prune_results.extend(prune_entries)

        return prune_results

    def _do_prune_entry(self, entry: ChangeLogEntry) -> bool:
        raise NotImplementedError


class CommitSubjectBodyPruner:  # pylint: disable=too-few-public-methods
    """Pruning based on subject / body content"""

    def __init__(self, pattern) -> None:
        self.pattern = pattern
        self.regexp = re.compile(self.pattern)

    def _do_prune_entry(self, entry: ChangeLogEntry) -> bool:
        return self.regexp.search(entry.subject) or self.regexp.search(entry.body)
