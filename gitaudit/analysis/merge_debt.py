"""This code helps identifying missing merges
in main that have already been merged in a
release branch
"""
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log, changelog_hydration
from gitaudit.git.controller import Git
from gitaudit.branch.tree import Tree


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
