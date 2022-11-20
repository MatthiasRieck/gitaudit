from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt.merge_debt import MergeDebt

from gitaudit.analysis.merge_debt.matchers import SameCommitMatcher, \
    DirectCherryPickMatcher, ThirdPartyCherryPickMatcher, FilesChangedMatcher, MatchConfidence

from .test_merge_debt_matchers.test_case_cherry_picked import \
    CHERRY_PICK_MAIN_LOG, CHERRY_PICK_DEV_LOG
from .test_merge_debt_matchers.test_case_cherry_picked_diff_numstat import \
    CHERRY_PICK_DIFF_MAIN_LOG, CHERRY_PICK_DIFF_DEV_LOG
from .test_merge_debt_matchers.test_case_files_changed_matcher import \
    FILES_CHANGED_MAIN_LOG, FILES_CHANGED_DEV_LOG

# main dev
#  |    |
# ffc---|---\
#  |    |    \
# a39  f53    |
#  | \  | \   |
#  |  \ |  \  |
#  |   \|   \ |
# f07  b8b   a21
#  |    | \   |
#  |    | eae /
#  |    | /  /
# d05  a6c  /
#  |   /   /
#  |  /   /
#  | /   /
# cfd   /
#  |   /
#  |  /
#  | /
# cf7

_ffc = {
    "sha": "ffc",
    "parent_shas": ["a39", "a21"]
}

_a39 = {
    "sha": "a39",
    "parent_shas": ["f07", "b8b"]
}

_f07 = {
    "sha": "f07",
    "parent_shas": ["d05"]
}

_d05 = {
    "sha": "d05",
    "parent_shas": ["cfd"]
}

_cfd = {
    "sha": "cfd",
    "parent_shas": ["cf7"]
}

_cf7 = {
    "sha": "cf7",
    "parent_shas": []
}

_f53 = {
    "sha": "f53",
    "parent_shas": ["b8b", "a21"]
}

_b8b = {
    "sha": "b8b",
    "parent_shas": ["a6c", "eae"]
}

_a6c = {
    "sha": "a6c",
    "parent_shas": ["cfd"]
}

_eae = {
    "sha": "eae",
    "parent_shas": ["a6c"]
}

_a21 = {
    "sha": "a21",
    "parent_shas": ["cf7"]
}

MAIN_LOG = [_ffc, _a39, _a21, _b8b, _eae, _a6c, _f07, _d05, _cfd, _cf7]
DEV_LOG = [_f53, _b8b, _eae, _a6c, _cfd, _a21, _cf7]


class TestMergeDebt(TestCase):
    def test_same_shas(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)

        merge_debt.execute_matcher(SameCommitMatcher())

        self.assertListEqual(
            merge_debt.head_buckets.entries,
            [],
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            ['d05', 'f07'],
        )

    def test_direct_cherry_picked_both_ways(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matcher(DirectCherryPickMatcher())

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            ['216', '3ac'],
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            ['48b', 'fd1'],
        )

    def test_direct_cherry_picked_head_to_base(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matcher(DirectCherryPickMatcher(
            head_to_base=True, base_to_head=False))

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            sorted(['216', '3ac', "562", "6b6", "4bf"]),
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            sorted(['48b', 'fd1', "9db", "ad0", "8d0"]),
        )

    def test_direct_cherry_picked_base_to_head(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matcher(DirectCherryPickMatcher(
            head_to_base=False, base_to_head=True))

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            sorted(['216', '3ac', "8bb", "4c2", "9fb"]),
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            sorted(['48b', 'fd1', "d91", "99f", "a34"]),
        )

    def test_third_party_cherry_pick(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matcher(ThirdPartyCherryPickMatcher())

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            sorted(['3ac', "8bb", "4c2", "9fb", "562", "6b6", "4bf"]),
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            sorted(['48b', "d91", "99f", "a34", "9db", "ad0", "8d0"]),
        )

    def test_multiple_matchers(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matchers([
            DirectCherryPickMatcher(),
            ThirdPartyCherryPickMatcher(),
        ])

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            sorted(['3ac']),
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            sorted(['48b']),
        )

    def test_diff_numstat(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DIFF_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DIFF_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matcher(DirectCherryPickMatcher())

        self.assertEqual(
            merge_debt.report.entries[0].match.base.sha,
            "a19",
        )
        self.assertEqual(
            merge_debt.report.entries[0].match.head.sha,
            "a6c",
        )

    def test_files_changed_with_add_del(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log)
        merge_debt.execute_matcher(FilesChangedMatcher())

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            ['873', 'f65'],
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            ['1e2', '657'],
        )

    def test_files_changed_without_add_del(self):
        main_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_MAIN_LOG),
        )
        dev_log = linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_DEV_LOG),
        )

        merge_debt = MergeDebt(dev_log, main_log, prunable_confidences=[
                               MatchConfidence.GOOD])
        merge_debt.execute_matcher(
            FilesChangedMatcher(with_additions_deletions=False))

        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.head_buckets.entries))),
            sorted(['873', '233']),
        )
        self.assertListEqual(
            sorted(list(map(lambda x: x.merge_commit.sha,
                   merge_debt.base_buckets.entries))),
            sorted(['9db', '657']),
        )
