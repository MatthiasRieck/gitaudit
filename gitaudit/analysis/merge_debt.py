"""This code helps identifying missing merges
in main that have already been merged in a
release branch
"""
from __future__ import annotations
from typing import List

from pydantic import BaseModel, Field

from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log, changelog_hydration
from gitaudit.git.controller import Git
from gitaudit.branch.tree import Tree

from gitaudit.git.change_log_entry import ChangeLogEntry


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
