"""This code helps identifying missing merges
in main that have already been merged in a
release branch
"""
from __future__ import annotations
from typing import List

from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log, changelog_hydration
from gitaudit.git.controller import Git
from gitaudit.branch.tree import Tree

from .matchers import Matcher
from .buckets import BucketList


def get_head_base_hier_logs(git: Git, head_ref: str, base_ref: str):
    """Gets the head and base hierarchy logs from a git instance
    as preparation for the merge debt analysis

    Args:
        git (Git): Git instance
        head_ref (str): name of the head ref
        base_ref (str): name of the base ref

    Returns:
        Tuple[List[ChangeLogEntry], List[ChangeLogEntry]]: head and base
            hierarchy log
    """
    head_hier_log = linear_log_to_hierarchy_log(git.log_parentlog(head_ref))
    base_hier_log = linear_log_to_hierarchy_log(git.log_parentlog(base_ref))

    tree = Tree()
    tree.append_log(base_hier_log, base_ref)
    tree.append_log(head_hier_log, head_ref)

    ref_segment_map = {
        x.branch_name: x for x in tree.root.children.values()
    }

    head_segment = ref_segment_map[head_ref]
    base_segment = ref_segment_map[base_ref]

    head_hier_log = changelog_hydration(
        head_segment.entries,
        git,
    )
    base_hier_log = changelog_hydration(
        base_segment.entries,
        git,
    )

    return head_hier_log, base_hier_log


class MergeDebt:
    """Calculates the merge debt by finding commits that are merged in head but not in base
    """

    def __init__(self, head_hier_log, base_hier_log) -> None:
        self.head_hier_log = head_hier_log
        self.base_hier_log = base_hier_log

        self.head_buckets = BucketList(self.head_hier_log)
        self.base_buckets = BucketList(self.base_hier_log)

        self.matches = []

    def ignore_shas(self, head_shas, base_shas=None):
        """Ability to set shas to be ignored for head and base. These are pruned and no longer
        part of the analysis.
        """
        for sha in head_shas:
            self.prune_head_sha(sha)

        if not base_shas:
            base_shas = []

        for sha in base_shas:
            self.prune_base_sha(sha)

    def prune_head_sha(self, sha):
        """Prunes a sha from the head bucket list

        Args:
            sha (str): sha to be pruned
        """
        self.head_buckets.prune_sha(sha)

    def prune_base_sha(self, sha):
        """Prunes a sha from the base bucket list

        Args:
            sha (str): sha to be pruned
        """
        self.base_buckets.prune_sha(sha)

    def execute_matcher(self, matcher: Matcher, prune=True):
        """Executes a matcher

        Args:
            matcher (Matcher): Matcher which will return commit match results
            prune (bool, optional): Whether or not the match results shall be prune immediately.
                Defaults to True.
        """
        sub_matches = matcher.match(
            self.head_buckets.entries, self.base_buckets.entries)

        self.matches.extend(sub_matches)

        if not prune:
            return

        for match in sub_matches:
            self.prune_head_sha(match.head.sha)
            self.prune_base_sha(match.base.sha)

    def execute_matchers(self, matchers: List[Matcher], prune=True):
        """Executed a list of matchers

        Args:
            matchers (List[Matcher]): List of matcher which will return commit match results
            prune (bool, optional): Whether or not the match results shall be prune immediately.
                Defaults to True.
        """
        for matcher in matchers:
            self.execute_matcher(matcher, prune)