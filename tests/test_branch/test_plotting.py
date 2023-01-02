from unittest import TestCase
from gitaudit.branch.tree import Tree
from gitaudit.branch.plotting import TreePlot
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.git.change_log_entry import ChangeLogEntry
from tests.test_custom_assert import assert_equal_svg


def get_hier_log(data):
    lin_log = list(map(
        lambda x: ChangeLogEntry.from_head_log_text(x),
        data,
    ))
    return linear_log_to_hierarchy_log(lin_log)


class TestTreePlot(TestCase):
    def test_initial(self):
        EXAMPLE_A = [
            "d[c]",
            "c[b]",
            "b[a]",
            "a[]",
        ]
        hier_log = get_hier_log(EXAMPLE_A)

        tree = Tree()
        tree.append_log(hier_log, 'main')

        plot = TreePlot(tree)

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (1, -4)
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main'],
        )

    def test_add_branch_off(self):
        EXAMPLE = [
            "d[c]",
            "c[b]",
            "b[a]",
            "a[]",
        ]
        EXAMPLE_BRANCH = [
            "f[e]",
            "e[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_branch = get_hier_log(EXAMPLE_BRANCH)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')

        plot = TreePlot(tree)

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (1, -2),
                "branch": (2, -4)
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch'],
        )

    def test_across_branch_point(self):
        EXAMPLE = [
            "d[c](2022-01-04)",
            "c[b](2022-01-03)",
            "b[a](2022-01-02)",
            "a[](2022-01-01)",
        ]
        EXAMPLE_BRANCH = [
            "ab[f](2022-01-05)",
            "f[e](2022-01-04)",
            "e[b](2022-01-03)",
            "b[a](2022-01-02)",
            "a[](2022-01-01)",
        ]
        EXAMPLE_HOTFIX = [
            "4[e](2022-01-04)",
            "e[b](2022-01-03)",
            "b[a](2022-01-02)",
            "a[](2022-01-01)",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_branch = get_hier_log(EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        plot = TreePlot(tree)

        self.assertDictEqual(
            plot._get_end_seg_counts(),
            {
                "main": (1, -2),
                "branch": (3, -5),
                "hotfix": (3, -4),
            }
        )
        self.assertEqual(
            plot.determine_ref_name_order(),
            ['main', 'branch', 'hotfix'],
        )

        assert_equal_svg(plot.create_svg())
