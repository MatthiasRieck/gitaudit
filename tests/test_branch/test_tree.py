from unittest import TestCase
from gitaudit.branch.tree import Tree
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.git.change_log_entry import ChangeLogEntry


def get_hier_log(data):
    lin_log = list(map(
        lambda x: ChangeLogEntry.from_head_log_text(x),
        data,
    ))
    return linear_log_to_hierarchy_log(lin_log)


class TestTree(TestCase):
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

        self.assertEqual(
            tree.root.shas,
            ['d', 'c', 'b', 'a'],
        )

    def test_add_longer(self):
        EXAMPLE = [
            "d[c]",
            "c[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE[-2:])
        hier_log_longer = get_hier_log(EXAMPLE)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_longer, 'main')

        self.assertEqual(
            tree.root.shas,
            ['d', 'c', 'b', 'a'],
        )

    def test_add_shorter(self):
        EXAMPLE = [
            "d[c]",
            "c[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_short = get_hier_log(EXAMPLE[-2:])

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_short, 'main')

        self.assertEqual(
            tree.root.shas,
            ['d', 'c', 'b', 'a'],
        )

    def test_add_same(self):
        EXAMPLE = [
            "d[c]",
            "c[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_same = get_hier_log(EXAMPLE)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_same, 'main')

        self.assertEqual(
            tree.root.shas,
            ['d', 'c', 'b', 'a'],
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

        self.assertEqual(
            tree.root.shas,
            ['b', 'a'],
        )
        self.assertEqual(
            tree.root.children['c'].shas,
            ['d', 'c'],
        )
        self.assertEqual(
            tree.root.children['e'].shas,
            ['f', 'e'],
        )

        for seg in tree.iter_segments():
            assert seg.shas in [
                ['b', 'a'],
                ['d', 'c'],
                ['f', 'e'],
            ]

    def test_across_branch_point(self):
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
        EXAMPLE_HOTFIX = [
            "4[e]",
            "e[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_branch = get_hier_log(EXAMPLE_BRANCH)
        hier_log_hotfix = get_hier_log(EXAMPLE_HOTFIX)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_hotfix, 'hotfix')

        self.assertEqual(
            tree.root.shas,
            ['b', 'a'],
        )
        self.assertEqual(
            tree.root.children['c'].shas,
            ['d', 'c'],
        )
        self.assertEqual(
            tree.root.children['e'].shas,
            ['e'],
        )
        self.assertEqual(
            tree.root.children['e'].children['f'].shas,
            ['f'],
        )
        self.assertEqual(
            tree.root.children['e'].children['4'].shas,
            ['4'],
        )

    def test_extend_branch_off(self):
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
        EXAMPLE_BRANCH_EXTEND = [
            "3[4]",
            "4[f]",
            "f[e]",
            "e[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_branch = get_hier_log(EXAMPLE_BRANCH)
        hier_log_branch_extend = get_hier_log(EXAMPLE_BRANCH_EXTEND)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_branch_extend, 'branch')

        self.assertEqual(
            tree.root.shas,
            ['b', 'a'],
        )
        self.assertEqual(
            tree.root.children['c'].shas,
            ['d', 'c'],
        )
        self.assertEqual(
            tree.root.children['e'].shas,
            ['3', '4', 'f', 'e'],
        )

    def test_add_branch_already_at_branch_point(self):
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
        EXAMPLE_BRANCH_TRIPLE = [
            "4[3]",
            "3[b]",
            "b[a]",
            "a[]",
        ]
        hier_log_root = get_hier_log(EXAMPLE)
        hier_log_branch = get_hier_log(EXAMPLE_BRANCH)
        hier_log_triple = get_hier_log(EXAMPLE_BRANCH_TRIPLE)

        tree = Tree()
        tree.append_log(hier_log_root, 'main')
        tree.append_log(hier_log_branch, 'branch')
        tree.append_log(hier_log_triple, 'triple')

        self.assertEqual(
            tree.root.shas,
            ['b', 'a'],
        )
        self.assertEqual(
            tree.root.children['c'].shas,
            ['d', 'c'],
        )
        self.assertEqual(
            tree.root.children['e'].shas,
            ['f', 'e'],
        )
        self.assertEqual(
            tree.root.children['3'].shas,
            ['4', '3'],
        )
