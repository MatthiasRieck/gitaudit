from unittest import TestCase
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log, hierarchy_log_to_linear_log
from gitaudit.git.change_log_entry import ChangeLogEntry


class TestLinearLogToHierarchyLog(TestCase):
    def test_example_a(self):
        EXAMPLE_A = [
            "d[c]",
            "c[b]",
            "b[a]",
            "a[]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_A))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        self.assertListEqual(lin_log, hier_log)

    def test_example_b(self):
        EXAMPLE_B = [
            "d[b, c]",
            "c[a]",
            "b[a]",
            "a[]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_B))
        lin_log_cpy = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_B))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        d, c, b, a = lin_log_cpy
        d.other_parents = [[c]]
        c.branch_offs = [a]

        self.assertEqual([d, b, a], hier_log)

    def test_example_c(self):
        EXAMPLE_C = [
            "a[b f]",
            "b[d c]",
            "d[e]",
            "c[d]",
            "e[1]",
            "1[]",
            "f[2 4]",
            "2[3]",
            "3[1]",
            "4[5]",
            "5[3]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        lin_log_cpy = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        a, b, d, c, e, one, f, two, three, four, five = lin_log_cpy

        c.branch_offs = [d]
        b.other_parents = [[c]]
        five.branch_offs = [three]
        f.other_parents = [[four, five]]
        three.branch_offs = [one]
        a.other_parents = [[f, two, three]]

        self.assertEqual([a, b, d, e, one], hier_log)

    def test_initil_commit(self):
        EXAMPLE_INITIAL_COMMIT = ["a[]"]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_INITIAL_COMMIT))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        self.assertListEqual(lin_log, hier_log)

    def test_octor_merge(self):
        EXAMPLE_OCTO_MERGE = [
            "a[b, c, d]",
            "b[]",
            "c[b]",
            "d[b]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_OCTO_MERGE))
        lin_log_cpy = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_OCTO_MERGE))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        a, b, c, d = lin_log_cpy

        c.branch_offs = [b]
        d.branch_offs = [b]
        a.other_parents = [[c], [d]]

        self.assertEqual([a, b], hier_log)

    def test_multi_merge(self):
        EXAMPLE_MULTI_MERGE = [
            "a[b e]",
            "b[c f]",
            "c[]",
            "e[f]",
            "f[c]",
        ]
        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_MULTI_MERGE))
        lin_log_cpy = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_MULTI_MERGE))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        a, b, c, e, f = lin_log_cpy

        f.branch_offs = [c]
        b.other_parents = [[f]]
        e.branch_offs = [f]
        a.other_parents = [[e]]

        self.assertEqual([a, b, c], hier_log)

    def test_parent_sha_already_taken(self):
        EXAMPLE_MULTI_MERGE = [
            "2b2[c9c 2ae]",
            "c9c[63b d86]",
            "63b[]",
            "2ae[63b d86]",
            "d86[63b]",
        ]
        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_MULTI_MERGE))
        lin_log_cpy = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_MULTI_MERGE))
        hier_log = linear_log_to_hierarchy_log(lin_log)

        _2b2, _c9c, _63b, _2ae, _d86 = lin_log_cpy

        _d86.branch_offs = [_63b]
        _c9c.other_parents = [[_d86]]
        _2ae.branch_offs = [_63b, _d86]
        _2b2.other_parents = [[_2ae]]

        self.assertEqual([_2b2, _c9c, _63b], hier_log)


class TestHierarchyLogToLinearLog(TestCase):
    def test_multi_merge(self):
        EXAMPLE_MULTI_MERGE = [
            "a[b e]",
            "b[c f]",
            "c[]",
            "e[f]",
            "f[c]",
        ]
        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_MULTI_MERGE))
        hier_log = linear_log_to_hierarchy_log(lin_log)
        lin_log_cpy = hierarchy_log_to_linear_log(hier_log)

        self.assertListEqual(
            ['a', 'e', 'b', 'f', 'c'],
            list(map(lambda x: x.sha, lin_log_cpy))
        )

    def test_example_c(self):
        EXAMPLE_C = [
            "a[b f]",
            "b[d c]",
            "d[e]",
            "c[d]",
            "e[1]",
            "1[]",
            "f[2 4]",
            "2[3]",
            "3[1]",
            "4[5]",
            "5[3]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        hier_log = linear_log_to_hierarchy_log(lin_log)
        lin_log_cpy = hierarchy_log_to_linear_log(hier_log)

        self.assertListEqual(
            ['a', 'f', '4', '5', '2', '3', 'b', 'c', 'd', 'e', '1'],
            list(map(lambda x: x.sha, lin_log_cpy))
        )

    def test_initil_commit(self):
        EXAMPLE_INITIAL_COMMIT = ["a[]"]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_INITIAL_COMMIT))
        hier_log = linear_log_to_hierarchy_log(lin_log)
        lin_log_cpy = hierarchy_log_to_linear_log(hier_log)

        self.assertListEqual(
            ['a'],
            list(map(lambda x: x.sha, lin_log_cpy))
        )

    def test_octor_merge(self):
        EXAMPLE_OCTO_MERGE = [
            "a[b, c, d]",
            "b[]",
            "c[b]",
            "d[b]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_OCTO_MERGE))
        hier_log = linear_log_to_hierarchy_log(lin_log)
        lin_log_cpy = hierarchy_log_to_linear_log(hier_log)

        self.assertListEqual(
            ['a', 'c', 'd', 'b'],
            list(map(lambda x: x.sha, lin_log_cpy))
        )
