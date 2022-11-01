"""Calculate Branch Trees
"""

from __future__ import annotations

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from gitaudit.git.change_log_entry import ChangeLogEntry


class Segment(BaseModel):
    """Class for Storing a Branch Segment
    """
    entries: List[ChangeLogEntry]
    children: Optional[Dict[str, Segment]] = Field(default_factory=dict)
    branch_name: Optional[str]

    @property
    def length(self):
        """Returns the number of entries in this segment
        """
        return len(self.entries)

    @property
    def first_sha(self):
        """Returns the sha of the first entry in this segment
        """
        return self.entries[0].sha

    @property
    def last_sha(self):
        """Returns the sha of the last entry in this segment
        """
        return self.entries[-1].sha

    @property
    def shas(self):
        """Returns all shas in this segment as a list
        """
        return list(map(lambda x: x.sha, self.entries))


class Tree(BaseModel):
    """Branching tree out of segments
    """
    root: Segment = None

    def append_log(self, hier_log: List[ChangeLogEntry], branch_name: str):
        """Append a new hierarchy log history to the tre

        Args:
            hier_log (List[ChangeLogEntry]): to be appended log
            branch_name (str): name of the branch / ref
        """
        new_segment = Segment(
            entries=hier_log,
            branch_name=branch_name,
        )

        if not self.root:
            self.root = new_segment
        else:
            self._merge_segment(new_segment)

    def _merge_segment(self, new_segment: Segment):
        index = 0

        assert self.root.entries[0].sha == new_segment.entries[0].sha, \
            "Initial shas do not match which is a prerequisite!"

        parent_segment = None
        current_segment = self.root

        while new_segment:

            while len(current_segment.entries) > index \
                    and len(new_segment.entries) > index \
                    and current_segment.entries[index].sha == new_segment.entries[index].sha:
                index += 1

            if len(new_segment.entries) <= index:
                # The new segment does not exceed the exiting one
                # --> no action necessary
                new_segment = None
            elif len(current_segment.entries) <= index:
                # the new segment exceeds the existing one
                # --> replace the existing one with the new one
                if current_segment.children:
                    # replace current segment
                    new_segment = Segment(
                        entries=new_segment.entries[index:],
                        branch_name=new_segment.branch_name,
                    )

                    if new_segment.first_sha in current_segment.children:
                        parent_segment = current_segment
                        current_segment = current_segment.children[new_segment.first_sha]
                        index = 0
                    else:
                        current_segment.children[new_segment.first_sha] = new_segment
                        new_segment = None
                else:
                    if parent_segment:
                        parent_segment.children[new_segment.first_sha] = new_segment
                        new_segment = None
                    else:
                        self.root = new_segment
                        new_segment = None
            else:
                current_segment_pre = Segment(
                    entries=current_segment.entries[0:index],
                    branch_name=current_segment.branch_name,
                )
                current_segment_post = Segment(
                    entries=current_segment.entries[index:],
                    branch_name=current_segment.branch_name,
                    children=current_segment.children,
                )
                new_segment_post = Segment(
                    entries=new_segment.entries[index:],
                    branch_name=new_segment.branch_name,
                )

                current_segment_pre.children[current_segment_post.first_sha] = current_segment_post
                current_segment_pre.children[new_segment_post.first_sha] = new_segment_post

                if parent_segment:
                    parent_segment.children[current_segment_pre.first_sha] = current_segment_pre
                    new_segment = None
                else:
                    self.root = current_segment_pre
                    new_segment = None

    def iter_segments(self):
        """Iterate Tree Segments

        Yields:
            Segment: Iterated Tree Segment
        """
        queue = [self.root]

        while queue:
            seg = queue.pop(0)
            yield seg
            queue.extend(seg.children.values())
