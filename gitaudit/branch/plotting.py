"""Plots a Tree
"""

from typing import List, Dict, Tuple

from .tree import Tree


class TreePlot:  # pylint: disable=too-few-public-methods
    """Class for plotting a branching tree
    """

    def __init__(self, tree: Tree) -> None:
        self.tree = tree

    def _get_end_seg_counts(self) -> Dict[str, Tuple[int, int]]:
        """For the given tree return the segment / sha count from each end point to the root

        Returns:
            Dict[str, Tuple[int, int]]: Seg / sha count distance information from the root
        """
        end_sha_seg_map = {
            seg.end_sha: seg for seg in self.tree.flatten_segments()
        }
        end_segments = self.tree.end_segments()
        end_ref_name_seg_map = {x.branch_name: x for x in end_segments}

        root_ref_name = self.tree.root.branch_name
        assert root_ref_name in end_ref_name_seg_map
        root_end_segment = end_ref_name_seg_map[root_ref_name]

        ref_name_counts = {}

        for segment in end_segments:
            curr_segment = segment
            seg_count = 1
            sha_count = curr_segment.length

            while curr_segment != root_end_segment:
                if curr_segment.branch_name != root_ref_name:
                    # go down
                    curr_segment = end_sha_seg_map[curr_segment.start_entry.parent_shas[0]]
                    if curr_segment.branch_name != root_ref_name:
                        seg_count += 1
                        sha_count += curr_segment.length
                else:
                    curr_segment = list(filter(
                        lambda x: x.branch_name == root_ref_name, curr_segment.children.values()
                    ))[0]
                    seg_count += 1
                    sha_count += curr_segment.length

            ref_name_counts[segment.branch_name] = (seg_count, -sha_count)

        return ref_name_counts

    def determine_ref_name_order(self) -> List[str]:
        """Based on branching segments and number of commit in each segment determine the optimal
        ref name order for plotting

        Returns:
            List[str]: Optimal Ref Name Order
        """
        ref_name_counts = self._get_end_seg_counts()
        end_ref_names = list(ref_name_counts)

        return sorted(end_ref_names, key=lambda x: ref_name_counts[x])
