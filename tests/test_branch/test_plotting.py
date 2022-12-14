from unittest import TestCase
from gitaudit.branch.tree import Tree
from gitaudit.branch.plotting import TreePlot
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.git.change_log_entry import ChangeLogEntry
from tests.test_custom_assert import assert_equal_svg
from svgdiagram.elements.circle import Circle
from svgdiagram.elements.group import Group
from svgdiagram.elements.multi_line_text import MultiLineText


def get_hier_log(data):
    lin_log = list(map(
        lambda x: ChangeLogEntry.from_head_log_text(x),
        data,
    ))
    return linear_log_to_hierarchy_log(lin_log)


NEW_EXAMPLE = [
    "d[c](2022-01-04)",
    "c[b](2022-01-03)",
    "b[a](2022-01-02)",
    "a[](2022-01-01)",
]
NEW_EXAMPLE_BRANCH = [
    "ab[f](2022-01-05)",
    "f[e](2022-01-04)",
    "e[34](2022-01-03)",
    "34[b](2022-01-02T10:00)",
    "b[a](2022-01-02)",
    "a[](2022-01-01)",
]
NEW_EXAMPLE_HOTFIX = [
    "4[e](2022-01-04)",
    "e[34](2022-01-03)",
    "34[b](2022-01-02T10:00)",
    "b[a](2022-01-02)",
    "a[](2022-01-01)",
]
NEW_EXAMPLE_HOTFIX_2 = [
    "def[da](2022-01-07)",
    "da[de](2022-01-06)",
    "de[f](2022-01-05)",
    "f[e](2022-01-04)",
    "e[34](2022-01-03)",
    "34[b](2022-01-02T10:00)",
    "b[a](2022-01-02)",
    "a[](2022-01-01)",
]


class TestTreePlot(TestCase):
    def test_initial(self):
        hier_log = get_hier_log(NEW_EXAMPLE)

        tree = Tree()
        tree.append_log(hier_log, 'main')

        plot = TreePlot(tree)

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, True, 1, -4)
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main'],
        )

    def test_add_branch_off(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')

        plot = TreePlot(tree)

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, True, 1, -2),
                "branch": (172800, True, 2, -6)
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch'],
        )

    def test_across_branch_point(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(tree, active_refs=['main', 'branch', 'hotfix'])

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, False, 1, -2),
                "branch": (172800, False, 3, -6),
                "hotfix": (172800, False, 3, -5),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot)

        self.assertEqual(
            plot.directly_connected_to_root_refs,
            ['main', 'branch']
        )

    def test_sha_svg_append_callback(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(
            tree,
            sha_svg_append_callback=lambda _: [
                Circle(0, 0, 10), Circle(0, 0, 10)],
            active_refs=['main', 'branch', 'hotfix'],
        )

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, False, 1, -2),
                "branch": (172800, False, 3, -6),
                "hotfix": (172800, False, 3, -5),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot)

    def test_show_commit_callback(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(
            tree,
            show_commit_callback=lambda _: True,
            active_refs=['main', 'branch', 'hotfix'],
        )

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, False, 1, -2),
                "branch": (172800, False, 3, -6),
                "hotfix": (172800, False, 3, -5),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot)

    def test_show_commit_callback_sha_svg_append_callback(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(
            tree,
            show_commit_callback=lambda _: True,
            sha_svg_append_callback=lambda _: [
                Circle(0, 0, 10), Circle(0, 0, 10)],
            active_refs=['main', 'branch', 'hotfix'],
        )

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, False, 1, -2),
                "branch": (172800, False, 3, -6),
                "hotfix": (172800, False, 3, -5),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot)

    def test_ref_name_formatting_callback(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(
            tree,
            ref_name_formatting_callback=lambda ref_name, head_entry: Group([
                Circle(0, 0, 40),
                MultiLineText.from_text(
                    0, 0, f"{ref_name}\n({head_entry.sha[0:7]})"),
            ]),
            active_refs=['main', 'branch', 'hotfix'],
        )

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, False, 1, -2),
                "branch": (172800, False, 3, -6),
                "hotfix": (172800, False, 3, -5),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot)

    def test_active_refs(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(tree, active_refs=['main', 'branch'])

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (0, False, 1, -2),
                "branch": (172800, False, 3, -6),
                "hotfix": (172800, True, 3, -5),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot)

    def test_active_refs_branch_ordering(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)
        hier_log_hotfix_2 = get_hier_log(NEW_EXAMPLE_HOTFIX_2)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')
        tree.append_log(hier_log_hotfix_2, 'hotfix_2')

        plot = TreePlot(tree, active_refs=['main', 'branch'])

        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix', 'hotfix_2'],
        )

        assert_equal_svg(plot)

        self.assertEqual(
            plot.directly_connected_to_root_refs,
            ['main', 'branch']
        )

    def test_ref_color_map(self):
        hier_log_root = get_hier_log(NEW_EXAMPLE)
        hier_log_branch = get_hier_log(NEW_EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(NEW_EXAMPLE_HOTFIX)
        hier_log_hotfix_2 = get_hier_log(NEW_EXAMPLE_HOTFIX_2)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')
        tree.append_log(hier_log_hotfix_2, 'hotfix_2')

        plot = TreePlot(
            tree,
            active_refs=['main', 'branch'],
            ref_color_map={
                "main": "#bae1ff",
                "branch": "#baffc9",
                "hotfix": "#ffdfba",
                "hotfix_2": "#ffb3ba",
            },
            graph_stroke_width_px=3,
        )

        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix', 'hotfix_2'],
        )

        assert_equal_svg(plot)

        self.assertEqual(
            plot.directly_connected_to_root_refs,
            ['main', 'branch']
        )

    def test_linear_correction(self):
        hier_log_root = get_hier_log([
            "d[a](2022-01-04)",
            "a[](2022-01-01)",
        ])
        hier_log_branch = get_hier_log([
            "c[a](2022-01-02)",
            "a[](2022-01-01)",
        ])

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')

        plot = TreePlot(
            tree,
            active_refs=['main', 'branch'],
            sha_svg_append_callback=lambda x:
                [Circle(0, 0, 10)]*8 if x.sha == 'd' else [],
        )

        assert_equal_svg(plot)
