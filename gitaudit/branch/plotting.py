"""Plots a Tree
"""

from datetime import timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from svgdiagram.elements.circle import Circle
from svgdiagram.elements.rect import Rect
from svgdiagram.elements.group import Group, TranslateTransform
from svgdiagram.elements.path import Path
from svgdiagram.elements.svg import Svg
from svgdiagram.elements.svg_element import SvgElement
from svgdiagram.elements.text import Text, HorizontalAlignment, VerticalAlignment

from gitaudit.git.change_log_entry import ChangeLogEntry
from .tree import Tree


SECONDS_IN_DAY = timedelta(days=1).total_seconds()
MAX_GAP = 50


@dataclass
class TreeLaneItem:
    """TreeLaneItem
    """
    entry: ChangeLogEntry
    ypos: Optional[float] = None
    offset: Optional[float] = None
    svgs: List[SvgElement] = field(default_factory=list)

    @property
    def id(self):  # pylint: disable=invalid-name
        """ID of the tree lane item
        """
        return self.entry.sha

    @property
    def date_time(self):
        """Date Time of the tree lane item
        """
        return self.entry.commit_date

    @property
    def pos_info(self):
        """position info of the tree lane item
        """
        return self.ypos, self.offset


@dataclass
class TreeConnection:
    """Tree Connection
    """
    from_id: str
    to_id: str


class TreeLane:  # pylint: disable=too-few-public-methods
    """Tree Lane
    """

    def __init__(self, ref_name: str, xpos: float, extend_to_top: bool = True) -> None:
        self.ref_name = ref_name
        self.items = []

        self.xpos = xpos
        self.extend_to_top = extend_to_top

    def append_item(self, item: TreeLaneItem):
        """Append tree lane item

        Args:
            item (TreeLaneItem): New tree item
        """
        self.items.append(item)


class TreePlot(Svg):  # pylint: disable=too-many-instance-attributes
    """Class for plotting a branching tree
    """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            tree: Tree,
            active_refs: List[str] = None,
            column_spacing: float = 200.0,
            show_commit_callback=None,
            sha_svg_append_callback=None,
            ref_name_formatting_callback=None,
    ) -> None:
        super().__init__()
        self.tree = tree
        self.active_refs = active_refs if active_refs else []
        self.column_spacing = column_spacing
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

        self.group_lines = Group()
        self.append_child(self.group_lines)

    def _sorted_items(self):
        return sorted(
            self.id_item_map.values(),
            key=lambda x: x.date_time,
            reverse=True,
        )

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
            lane.append_item(TreeLaneItem(entry=segment.end_entry))

            if self.show_commit_callback:
                for entry in segment.entries[1:]:
                    if self.show_commit_callback(entry):
                        lane.append_item(TreeLaneItem(entry=entry))

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

    def _create_commit_svg_element(self, xpos: float, ypos: float, entry: ChangeLogEntry):
        return_elems = []
        text = Text(
            xpos + 15,
            ypos,
            f"{entry.sha[0:7]} ({entry.commit_date.date().isoformat()})",
            horizontal_alignment=HorizontalAlignment.LEFT,
            font_family='monospace',
        )
        text_bounds = text.bounds
        text_width, text_height = text_bounds[1] - \
            text_bounds[0], text_bounds[3]-text_bounds[2]
        return_elems.append(Circle(xpos, ypos, 5))
        return_elems.append(Rect(xpos + 10, ypos - text_height/2-2, text_width+10,
                                 text_height+4, rx=8, ry=8, stroke="transparent"))
        return_elems.append(text)

        offset = 0
        if self.sha_svg_append_callback:
            elems = self.sha_svg_append_callback(entry)

            offset = text_height/2 + 2 + 10
            for elem in elems:
                bnds = elem.bounds
                return_elems.append(Group(
                    elem,
                    transforms=TranslateTransform(
                        dx=xpos - bnds[0] + 10,
                        dy=ypos - bnds[2] + offset,
                    ),
                ))

                offset += bnds[3]-bnds[2] + 10

        return return_elems, offset

    def _create_lane_head_svg_element(self, ypos: float, lane: TreeLane):
        if self.ref_name_formatting_callback:
            elem = self.ref_name_formatting_callback(
                lane.ref_name,
                lane.items[0].entry,
            )
            bnds = elem.bounds
            return Group(
                elem,
                transforms=TranslateTransform(
                    dx=lane.xpos - (bnds[0]+bnds[1]) / 2.0,
                    dy=ypos - bnds[3],
                )
            )

        return Text(
            lane.xpos, ypos, lane.ref_name,
            vertical_alignment=VerticalAlignment.BOTTOM,
            font_family='monospace',
        )

    def _calculate_positions(self):
        pass

    def _render_positions(self):
        pass

    def _render_connections(self):
        lane_prev_pos = {}

        for item in self._sorted_items():
            lane = self.id_lane_map[item.id]
            if lane.ref_name in lane_prev_pos:
                self.group_lines.append_child(Path(
                    points=[lane_prev_pos[lane.ref_name],
                            (lane.xpos, item.ypos)]
                ))
            else:
                self.group_lines.append_child(Path(
                    points=[(lane.xpos, 0), (lane.xpos, item.ypos)]
                ))
            lane_prev_pos[lane.ref_name] = (lane.xpos, item.ypos)

        # plot connections
        for connection in self.connections:
            f_lane = self.id_lane_map[connection.from_id]
            f_y, _ = self.id_item_map[connection.from_id].pos_info
            t_lane = self.id_lane_map[connection.to_id]
            t_y, _ = self.id_item_map[connection.to_id].pos_info
            self.group_lines.append_child(Path(
                points=[(f_lane.xpos, f_y), (t_lane.xpos, f_y),
                        (t_lane.xpos, t_y)],
                corner_radius=8,
            ))

    def _layout(self, x_con_min, x_con_max, y_con_min, y_con_max):
        """Creates Svg object out of tree information

        Returns:
            Svg: Svg Object
        """
        self._create_lanes()

        lane_progess_map = {}
        lane_initial_datetime_map = {
            x.ref_name: x.items[0].date_time for x in self.lanes
        }

        curr_offset_date = max(lane_initial_datetime_map.values())
        curr_offset = 30

        day_scale = 80

        for index, lane in enumerate(self.lanes):
            lane.xpos = index*self.column_spacing
            lypos = -10
            self.append_child(
                self._create_lane_head_svg_element(lypos, lane))

        from_ids = {x.from_id: x for x in self.connections}

        # plot items
        for item in self._sorted_items():
            lane = self.id_lane_map[item.id]

            days_from_offset = (
                curr_offset_date-item.date_time
            ).total_seconds() / SECONDS_IN_DAY
            delta_offset = day_scale*days_from_offset

            delta_offset = min(delta_offset, MAX_GAP)

            curr_offset = curr_offset + delta_offset

            if item.id in from_ids:
                connect = from_ids[item.id]
                to_ypos, to_offset = self.id_item_map[connect.to_id].pos_info
                curr_offset = max(curr_offset, to_ypos + to_offset + 20)

            item.ypos = max(
                curr_offset,
                lane_progess_map[lane.ref_name] +
                10 if lane.ref_name in lane_progess_map else curr_offset,
            )

            return_elems, offset = self._create_commit_svg_element(
                lane.xpos, item.ypos, item.entry)
            item.svgs = return_elems
            item.offset = offset
            self.extend_childs(return_elems)

            curr_offset_date = item.date_time
            lane_progess_map[lane.ref_name] = item.ypos + offset

        self._render_connections()

        return super()._layout(x_con_min, x_con_max, y_con_min, y_con_max)
