from unittest import TestCase

from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt import \
    get_head_base_hier_logs,\
    BucketEntry,\
    get_sha_to_bucket_entry_map,\
    get_linear_bucket_list

MAIN_JSON_LOG = [
    {
        "sha": "d",
        "parent_shas": ["c"],
    },
    {
        "sha": "c",
        "parent_shas": ["b"],
    },
    {
        "sha": "b",
        "parent_shas": ["a"],
    },
    {
        "sha": "a",
        "parent_shas": [],
    },
]

RELEASE_JSON_LOG = [
    {
        "sha": "f",
        "parent_shas": ["e"],
    },
    {
        "sha": "e",
        "parent_shas": ["b"],
    },
    {
        "sha": "b",
        "parent_shas": ["a"],
    },
    {
        "sha": "a",
        "parent_shas": [],
    },
]


class MockGit:
    def __init__(self, ) -> None:
        self.ref_logs = {}

    def append_ref(self, name, json_log):
        self.ref_logs[name] = json_log
        self.ref_logs[json_log[0]['sha']] = json_log

    def log_parentlog(self, end_ref):
        return list(map(
            lambda x: ChangeLogEntry.parse_obj(x),
            self.ref_logs[end_ref],
        ))

    def log_changelog(self, end_ref, start_ref=False, first_parent=False, patch=False):
        return list(map(
            lambda x: ChangeLogEntry.parse_obj(x),
            self.ref_logs[end_ref],
        ))


class TestGetHeadBaseHierLogs(TestCase):
    def test_normal(self):
        mock_git = MockGit()
        mock_git.append_ref('main', MAIN_JSON_LOG)
        mock_git.append_ref('release', RELEASE_JSON_LOG)

        head, base = get_head_base_hier_logs(mock_git, 'release', 'main')
        self.assertListEqual(
            list(map(lambda x: x.sha, head)),
            ['f', 'e'],
        )
        self.assertListEqual(
            list(map(lambda x: x.sha, base)),
            ['d', 'c'],
        )


class TestBucketEntry(TestCase):
    def test_branched_version(self):
        # a
        # | \
        # |  \
        # b   f
        # |\  |\
        # | c 2 4
        # |/  | |
        # d   | 5
        # |   |/
        # e   3
        # |  /
        # |/
        # 1

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
        buckets = BucketEntry.list_from_change_log_list(hier_log)

        self.assertEqual(buckets[0].merge_sha, 'a')
        self.assertListEqual(buckets[0].branch_shas, [])
        self.assertListEqual(buckets[0].children_shas, ['f'])

        self.assertEqual(buckets[0].children[0].merge_sha, 'f')
        self.assertListEqual(
            buckets[0].children[0].branch_shas,
            ['2', '3', '4', '5'],
        )
        self.assertListEqual(buckets[0].children[0].children_shas, [])

        self.assertEqual(buckets[1].merge_sha, 'b')
        self.assertListEqual(buckets[1].branch_shas, ['c'])
        self.assertListEqual(buckets[1].children_shas, [])

        self.assertEqual(buckets[2].merge_sha, 'd')
        self.assertListEqual(buckets[2].branch_shas, [])
        self.assertListEqual(buckets[2].children_shas, [])

        self.assertEqual(buckets[3].merge_sha, 'e')
        self.assertListEqual(buckets[3].branch_shas, [])
        self.assertListEqual(buckets[3].children_shas, [])

        self.assertEqual(buckets[4].merge_sha, '1')
        self.assertListEqual(buckets[4].branch_shas, [])
        self.assertListEqual(buckets[4].children_shas, [])

    def test_simpler_version(self):
        # a
        # | \
        # |  \
        # b   f
        # |\  |
        # | c 2
        # |/  |
        # d   |
        # |   |
        # e   3
        # |  /
        # |/
        # 1

        EXAMPLE_C = [
            "a[b f]",
            "b[d c]",
            "d[e]",
            "c[d]",
            "e[1]",
            "1[]",
            "f[2]",
            "2[3]",
            "3[1]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        hier_log = linear_log_to_hierarchy_log(lin_log)
        buckets = BucketEntry.list_from_change_log_list(hier_log)

        self.assertEqual(buckets[0].merge_sha, 'a')
        self.assertListEqual(buckets[0].branch_shas, ['f', '2', '3'])
        self.assertListEqual(buckets[0].children_shas, [])

        self.assertEqual(buckets[1].merge_sha, 'b')
        self.assertListEqual(buckets[1].branch_shas, ['c'])
        self.assertListEqual(buckets[1].children_shas, [])

        self.assertEqual(buckets[2].merge_sha, 'd')
        self.assertListEqual(buckets[2].branch_shas, [])
        self.assertListEqual(buckets[2].children_shas, [])

        self.assertEqual(buckets[3].merge_sha, 'e')
        self.assertListEqual(buckets[3].branch_shas, [])
        self.assertListEqual(buckets[3].children_shas, [])

        self.assertEqual(buckets[4].merge_sha, '1')
        self.assertListEqual(buckets[4].branch_shas, [])
        self.assertListEqual(buckets[4].children_shas, [])


class TestBucketConversions(TestCase):
    def test_simple(self):
        # a
        # | \
        # |  \
        # b   f
        # |\  |
        # | c 2
        # |/  |
        # d   |
        # |   |
        # e   3
        # |  /
        # |/
        # 1

        EXAMPLE_C = [
            "a[b f]",
            "b[d c]",
            "d[e]",
            "c[d]",
            "e[1]",
            "1[]",
            "f[2]",
            "2[3]",
            "3[1]",
        ]

        lin_log = list(
            map(lambda x: ChangeLogEntry.from_head_log_text(x), EXAMPLE_C))
        hier_log = linear_log_to_hierarchy_log(lin_log)
        buckets = BucketEntry.list_from_change_log_list(hier_log)

        bucket_map, entry_map = get_sha_to_bucket_entry_map(buckets)

        self.assertListEqual(
            sorted(list(bucket_map)),
            ['1', '2', '3', 'a', 'b', 'c', 'd', 'e', 'f'],
        )
        self.assertListEqual(
            sorted(list(entry_map)),
            ['1', '2', '3', 'a', 'b', 'c', 'd', 'e', 'f'],
        )
        for sha, entry in entry_map.items():
            self.assertEqual(sha, entry.sha)
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_sha, get_linear_bucket_list(buckets)))),
            ['1', 'a', 'b', 'd', 'e'],
        )

    def test_branched_version(self):
        # a
        # | \
        # |  \
        # b   f
        # |\  |\
        # | c 2 4
        # |/  | |
        # d   | 5
        # |   |/
        # e   3
        # |  /
        # |/
        # 1

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
        buckets = BucketEntry.list_from_change_log_list(hier_log)

        bucket_map, entry_map = get_sha_to_bucket_entry_map(buckets)

        self.assertListEqual(
            sorted(list(bucket_map)),
            ['1', '2', '3', '4', '5', 'a', 'b', 'c', 'd', 'e', 'f'],
        )
        self.assertListEqual(
            sorted(list(entry_map)),
            ['1', '2', '3', '4', '5', 'a', 'b', 'c', 'd', 'e', 'f'],
        )
        for sha, entry in entry_map.items():
            self.assertEqual(sha, entry.sha)
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_sha, get_linear_bucket_list(buckets)))),
            ['1', 'a', 'b', 'd', 'e', 'f'],
        )
