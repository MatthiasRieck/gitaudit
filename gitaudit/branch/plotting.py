"""Plots a Tree
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from pydantic import BaseModel

from svgdiagram.elements.circle import Circle
from svgdiagram.elements.rect import Rect
from svgdiagram.elements.group import Group, TranslateTransform
from svgdiagram.elements.path import Path
from svgdiagram.elements.svg import Svg
from svgdiagram.elements.text import Text, HorizontalAlignment, VerticalAlignment

from gitaudit.git.change_log_entry import ChangeLogEntry
from .tree import Tree


SECONDS_IN_DAY = timedelta(days=1).total_seconds()
MAX_GAP = 50


class TreeLaneItem(BaseModel):
    """TreeLaneItem
    """
    id: str
    date_time: datetime
    item: ChangeLogEntry


class TreeConnection(BaseModel):
    """Tree Connection
    """
    from_id: str
    to_id: str


class TreeLane:  # pylint: disable=too-few-public-methods
    """Tree Lane
    """

    def __init__(self, ref_name: str, pos: float, extend_to_top: bool = True) -> None:
        self.ref_name = ref_name
        self.items = []

        self.pos = pos
        self.extend_to_top = extend_to_top

    def append_item(self, item: TreeLaneItem):
        """Append tree lane item

        Args:
            item (TreeLaneItem): New tree item
        """
        self.items.append(item)


class TreePlot:  # pylint: disable=too-many-instance-attributes
    """Class for plotting a branching tree
    """

    def __init__(
            self,
            tree: Tree,
            show_commit_callback=None,
            sha_svg_append_callback=None,
            ref_name_formatting_callback=None,
    ) -> None:
        self.tree = tree
        self.end_sha_seg_map = {
            seg.end_sha: seg for seg in self.tree.flatten_segments()
        }
        self.end_ref_name_seg_map = {
            x.branch_name: x for x in self.tree.flatten_segments()}

        self.show_commit_callback = show_commit_callback
        self.sha_svg_append_callback = sha_svg_append_callback
        self.ref_name_formatting_callback = ref_name_formatting_callback

        self.lanes = []
        self.connections = []
        self.laned_segment_end_shas = []
        self.id_item_map = {}
        self.id_lane_map = {}

    def _get_end_seg_counts(self) -> Dict[str, Tuple[int, int]]:
        """For the given tree return the segment / sha count from each end point to the root

        Returns:
            Dict[str, Tuple[int, int, int]]: second / Seg / sha count distance information
            from the root
        """
        root_ref_name = self.tree.root.branch_name
        assert root_ref_name in self.end_ref_name_seg_map
        root_end_segment = self.end_ref_name_seg_map[root_ref_name]

        ref_name_counts = {}

        for segment in self.end_ref_name_seg_map.values():
            curr_segment = segment
            seg_count = 1
            sha_count = curr_segment.length
            seconds_from_root_end = \
                int((root_end_segment.end_entry.commit_date -
                     curr_segment.end_entry.commit_date).total_seconds())

            while curr_segment.end_sha != root_end_segment.end_sha:
                if curr_segment.branch_name != root_ref_name:
                    # go down
                    curr_segment = self.end_sha_seg_map[curr_segment.start_entry.parent_shas[0]]
                    if curr_segment.branch_name != root_ref_name:
                        seg_count += 1
                        sha_count += curr_segment.length
                    else:
                        seconds_from_root_end = \
                            int((root_end_segment.end_entry.commit_date -
                                 curr_segment.end_entry.commit_date).total_seconds())
                else:
                    curr_segment = list(filter(
                        lambda x: x.branch_name == root_ref_name, curr_segment.children.values()
                    ))[0]
                    seg_count += 1
                    sha_count += curr_segment.length

            ref_name_counts[segment.branch_name] = (
                seconds_from_root_end, seg_count, -sha_count
            )

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

    def _create_lane(self, ref_name, hpos):
        print(f'Create Lane: {ref_name}')
        lane = TreeLane(ref_name, hpos)
        segment = self.end_ref_name_seg_map[ref_name]

        while segment:
            self.laned_segment_end_shas.append(segment.end_sha)
            lane.append_item(TreeLaneItem(
                id=segment.end_entry.sha,
                date_time=segment.end_entry.commit_date,
                item=segment.end_entry,
            ))

            if self.show_commit_callback:
                for entry in segment.entries[1:]:
                    if self.show_commit_callback(entry):
                        lane.append_item(TreeLaneItem(
                            id=entry.sha,
                            date_time=entry.commit_date,
                            item=entry,
                        ))

            if segment.start_entry.parent_shas:
                new_segment = self.end_sha_seg_map[segment.start_entry.parent_shas[0]]
                if new_segment.end_sha not in self.laned_segment_end_shas:
                    segment = new_segment
                else:
                    # need to create new connection here
                    self.connections.append(TreeConnection(
                        to_id=lane.items[-1].id,
                        from_id=segment.start_entry.parent_shas[0],
                    ))
                    segment = None
            else:
                segment = None

        return lane

    def _create_lanes(self) -> None:
        ref_order_names = self.determine_ref_name_order()

        for index, ref_name in enumerate(ref_order_names):
            lane = self._create_lane(ref_name, index * 300)

            for item in lane.items:
                self.id_item_map[item.id] = item
                self.id_lane_map[item.id] = lane

            self.lanes.append(lane)

    def create_svg(self) -> Svg:  # pylint: disable=too-many-locals, too-many-statements
        """Creates Svg object out of tree information

        Returns:
            Svg: Svg Object
        """
        self._create_lanes()

        lane_progess_map = {}
        # lane_datetime_map = {}
        lane_initial_datetime_map = {
            x.ref_name: x.items[0].date_time for x in self.lanes
        }
        lane_prev_pos = {}

        max_datetime = max(lane_initial_datetime_map.values())
        curr_offset_date = max_datetime
        curr_offset = 30

        day_scale = 80

        sorted_items = sorted(
            self.id_item_map.values(),
            key=lambda x: x.date_time,
            reverse=True,
        )

        id_locations = {}

        svg = Svg()
        group_lines = Group()
        svg.append_child(group_lines)

        for index, lane in enumerate(self.lanes):
            lxpos = index*200
            lypos = -10
            if self.ref_name_formatting_callback:
                elem = self.ref_name_formatting_callback(lane.ref_name)
                bnds = elem.bounds
                svg.append_child(Group(
                    elem,
                    transforms=TranslateTransform(
                        dx=lxpos - (bnds[0]+bnds[1]) / 2.0,
                        dy=lypos - bnds[3],
                    )
                ))
            else:
                svg.append_child(Text(
                    lxpos,
                    lypos,
                    lane.ref_name,
                    vertical_alignment=VerticalAlignment.BOTTOM,
                    font_family='monospace',
                ))

        from_ids = {x.from_id: x for x in self.connections}

        for item in sorted_items:
            lane = self.id_lane_map[item.id]
            lane_index = self.lanes.index(lane)

            days_from_offset = (
                curr_offset_date-item.date_time
            ).total_seconds() / SECONDS_IN_DAY
            delta_offset = day_scale*days_from_offset

            delta_offset = min(delta_offset, MAX_GAP)

            curr_offset = curr_offset + delta_offset

            if item.id in from_ids:
                connect = from_ids[item.id]
                _, to_ypos = id_locations[connect.to_id]
                curr_offset = max(curr_offset, to_ypos + 20)

            lane_offset = max(
                curr_offset,
                lane_progess_map[lane.ref_name] +
                10 if lane.ref_name in lane_progess_map else curr_offset,
            )

            curr_offset_date = item.date_time

            xpos = lane_index*200
            ypos = lane_offset
            id_locations[item.id] = (xpos, ypos)

            if lane.ref_name in lane_prev_pos:
                group_lines.append_child(Path(
                    points=[lane_prev_pos[lane.ref_name], (xpos, ypos)]
                ))
            else:
                group_lines.append_child(Path(
                    points=[(xpos, 0), (xpos, ypos)]
                ))
            lane_prev_pos[lane.ref_name] = (xpos, ypos)
            text = Text(
                xpos + 15,
                ypos,
                item.item.sha[0:7],
                horizontal_alignment=HorizontalAlignment.LEFT,
                font_family='monospace',
            )
            text_bounds = text.bounds
            text_width, text_height = text_bounds[1] - \
                text_bounds[0], text_bounds[3]-text_bounds[2]
            svg.append_child(Circle(xpos, ypos, 5))
            svg.append_child(Rect(xpos + 10, ypos - text_height/2-2, text_width+10,
                             text_height+4, rx=8, ry=8, stroke="transparent"))
            svg.append_child(text)

            offset = 0
            if self.sha_svg_append_callback:
                elems = self.sha_svg_append_callback(item.item)

                offset = text_height/2 + 2 + 10
                for elem in elems:
                    bnds = elem.bounds
                    svg.append_child(Group(
                        elem,
                        transforms=TranslateTransform(
                            dx=xpos - bnds[0] + 10,
                            dy=ypos - bnds[2] + offset,
                        ),
                    ))

                    offset += bnds[3]-bnds[2] + 10

            lane_progess_map[lane.ref_name] = lane_offset + offset

        for connection in self.connections:
            pos_from = id_locations[connection.from_id]
            pos_to = id_locations[connection.to_id]
            group_lines.append_child(Path(
                points=[
                    pos_from,
                    (pos_to[0], pos_from[1]),
                    pos_to,
                ],
                corner_radius=8,
            ))

        return svg
