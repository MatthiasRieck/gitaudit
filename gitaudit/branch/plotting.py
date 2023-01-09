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
    commit_text_svg: Optional[SvgElement] = None
    commit_circle_svg: Optional[SvgElement] = None
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
        self.ref_svg = None

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
            ref_color_map: Dict[str, str] = None,
            graph_stroke_width_px: int = 1,
            column_spacing: float = 200.0,
            apply_linear_vert_pos_correction: bool = True,
            show_commit_callback=None,
            sha_svg_append_callback=None,
            ref_name_formatting_callback=None,
    ) -> None:
        super().__init__()
        self.tree = tree
        self.active_refs = active_refs if active_refs else []
        self.ref_color_map = ref_color_map if ref_color_map else {}
        self.graph_stroke_width_px = graph_stroke_width_px
        self.apply_linear_vert_pos_correction = apply_linear_vert_pos_correction
        self.directly_connected_to_root_refs = []
        self.column_spacing = column_spacing
        self.end_sha_seg_map = {
            seg.end_sha: seg for seg in self.tree.flatten_segments()
        }
        self.end_ref_name_seg_map = {
            x.branch_name: x for x in self.tree.flatten_segments()}

        self.show_commit_callback = show_commit_callback
        self.sha_svg_append_callback = sha_svg_append_callback
        self.ref_name_formatting_callback = ref_name_formatting_callback

        self.lanes: List[TreeLane] = []
        self.connections = []
        self.laned_segment_end_shas = []
        self.id_item_map = {}
        self.id_lane_map = {}

        self.group_lines = Group()
        self.append_child(self.group_lines)

    def _sorted_items(self) -> List[TreeLaneItem]:
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
                seconds_from_root_end,
                segment.branch_name not in self.active_refs,
                seg_count,
                -sha_count
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
                    from_id = segment.start_entry.parent_shas[0]
                    self.connections.append(TreeConnection(
                        to_id=lane.items[-1].id,
                        from_id=from_id,
                    ))
                    if self.end_sha_seg_map[from_id].branch_name == self.tree.root.branch_name:
                        self.directly_connected_to_root_refs.append(ref_name)
                    segment = None
            else:
                segment = None

        return lane

    def _create_lanes(self) -> None:
        ref_order_names = self.determine_ref_name_order()
        self.directly_connected_to_root_refs.append(self.tree.root.branch_name)

        for index, ref_name in enumerate(ref_order_names):
            lane = self._create_lane(ref_name, index * 300)

            for item in lane.items:
                self.id_item_map[item.id] = item
                self.id_lane_map[item.id] = lane

            self.lanes.append(lane)

    def _create_commit_svg_elems(self):
        for item in self._sorted_items():
            lane = self.id_lane_map[item.id]
            ref_color = self.ref_color_map.get(lane.ref_name, 'black')
            if self.sha_svg_append_callback:
                item.svgs = self.sha_svg_append_callback(item.entry)

            item.commit_circle_svg = Circle(
                0, 0, 5,
                stroke=ref_color,
                stroke_width_px=self.graph_stroke_width_px,
            )

            text = Text(
                15,
                0,
                f"{item.entry.sha[0:7]} ({item.entry.commit_date.date().isoformat()})",
                horizontal_alignment=HorizontalAlignment.LEFT,
                font_family='monospace',
            )
            text_width, text_height = text.size
            rect = Rect(10, - text_height/2-2, text_width+10,
                        text_height+4, rx=8, ry=8, stroke="transparent")

            item.commit_text_svg = Group([rect, text])

    def _create_lane_ref_svg_elems(self):
        for lane in self.lanes:
            if self.ref_name_formatting_callback:
                lane.ref_svg = self.ref_name_formatting_callback(
                    lane.ref_name,
                    lane.items[0].entry,
                )
            else:
                lane.ref_svg = Text(
                    0, 0, lane.ref_name,
                    vertical_alignment=VerticalAlignment.BOTTOM,
                    font_family='monospace',
                )

    def _create_commit_svg_element(self, xpos: float, ypos: float, item: TreeLaneItem):
        return_elems = []

        _, text_height = item.commit_text_svg.size
        _, circle_height = item.commit_circle_svg.size

        commit_height = max(text_height, circle_height)

        return_elems.append(Group(
            item.commit_circle_svg,
            transforms=TranslateTransform(
                dx=xpos,
                dy=ypos,
            ),
        ))
        return_elems.append(Group(
            item.commit_text_svg,
            transforms=TranslateTransform(
                dx=xpos,
                dy=ypos,
            ),
        ))

        offset = commit_height/2 + 2 + 10
        for elem in item.svgs:
            bnds = elem.bounds
            return_elems.append(Group(
                elem,
                transforms=TranslateTransform(
                    dx=xpos - bnds[0] + 10,
                    dy=ypos - bnds[2] + offset,
                ),
            ))

            offset += bnds[3]-bnds[2] + 10

        return return_elems

    def _calculate_positions(self):  # pylint: disable=too-many-locals
        lane_progess_map = {}
        lane_initial_datetime_map = {
            x.ref_name: x.items[0].date_time for x in self.lanes
        }

        curr_offset_date = max(lane_initial_datetime_map.values())
        curr_offset = 30

        day_scale = 80

        for index, lane in enumerate(self.lanes):
            lane.xpos = index*self.column_spacing

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

            offset = 0
            if item.svgs:
                offset = 20
                for elem in item.svgs:
                    bnds = elem.bounds
                    offset += bnds[3]-bnds[2] + 10

            item.offset = offset

            curr_offset_date = item.date_time
            lane_progess_map[lane.ref_name] = item.ypos + offset

    def _linear_position_correction(self):
        if not self.apply_linear_vert_pos_correction:
            return

        items = self._sorted_items()
        for index, item in enumerate(items):
            if index in {0, len(items)-1}:
                continue

            lane = self.id_lane_map[item.id]

            prev_y = items[index+1].ypos
            prev_d = items[index+1].date_time
            next_y = items[index-1].ypos
            next_d = items[index-1].date_time

            prev_next_ts = (next_d-prev_d).total_seconds()

            if prev_next_ts >= 0.001:
                item.ypos = prev_y + (next_y-prev_y) * \
                    (item.date_time-prev_d).total_seconds() / prev_next_ts
            else:
                item.ypos = (prev_y + next_y) / 2.0

            item_lane_index = lane.items.index(item)
            if item_lane_index > 0:
                prev_lane_item = lane.items[item_lane_index-1]
                item.ypos = max(
                    item.ypos,
                    prev_lane_item.ypos + prev_lane_item.offset + 20,
                )

    def _render_lanes(self):
        for lane in self.lanes:
            if lane.ref_name in self.active_refs:
                ypos = -10
            else:
                ypos = lane.items[0].ypos-10

            bnds = lane.ref_svg.bounds
            self.append_child(Group(
                lane.ref_svg,
                transforms=TranslateTransform(
                    dx=lane.xpos - (bnds[0]+bnds[1]) / 2.0,
                    dy=ypos - bnds[3],
                )
            ))

    def _render_positions(self):
        for item in self._sorted_items():
            lane = self.id_lane_map[item.id]
            return_elems = self._create_commit_svg_element(
                lane.xpos, item.ypos, item)
            self.extend_childs(return_elems)

    def _render_connections(self):
        lane_prev_pos = {}

        for item in self._sorted_items():
            lane = self.id_lane_map[item.id]
            ref_color = self.ref_color_map.get(lane.ref_name, 'black')
            if lane.ref_name in lane_prev_pos:
                self.group_lines.append_child(Path(
                    points=[lane_prev_pos[lane.ref_name],
                            (lane.xpos, item.ypos)],
                    stroke=ref_color,
                    stroke_width_px=self.graph_stroke_width_px,
                ))
            else:
                offset = 0 if lane.ref_name in self.active_refs else lane.items[0].ypos
                self.group_lines.append_child(Path(
                    points=[(lane.xpos, offset-0),
                            (lane.xpos, item.ypos)],
                    stroke=ref_color,
                    stroke_width_px=self.graph_stroke_width_px,
                ))
            lane_prev_pos[lane.ref_name] = (lane.xpos, item.ypos)

        # plot connections
        for connection in self.connections:
            f_lane = self.id_lane_map[connection.from_id]
            f_y, _ = self.id_item_map[connection.from_id].pos_info
            t_lane = self.id_lane_map[connection.to_id]
            t_y, _ = self.id_item_map[connection.to_id].pos_info
            ref_color = self.ref_color_map.get(t_lane.ref_name, 'black')
            self.group_lines.append_child(Path(
                points=[(f_lane.xpos, f_y), (t_lane.xpos, f_y),
                        (t_lane.xpos, t_y)],
                corner_radius=8,
                stroke=ref_color,
                stroke_width_px=self.graph_stroke_width_px,
            ))

    def _layout(self, x_con_min, x_con_max, y_con_min, y_con_max):
        """Creates Svg object out of tree information

        Returns:
            Svg: Svg Object
        """
        self._create_lanes()
        self._create_lane_ref_svg_elems()
        self._create_commit_svg_elems()
        self._calculate_positions()
        self._linear_position_correction()
        self._render_lanes()
        self._render_positions()
        self._render_connections()

        return super()._layout(x_con_min, x_con_max, y_con_min, y_con_max)
