from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt.merge_debt import MergeDebt

from gitaudit.analysis.merge_debt.matchers import SameCommitMatcher

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
