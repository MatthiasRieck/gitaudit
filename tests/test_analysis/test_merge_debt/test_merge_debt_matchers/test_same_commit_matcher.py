from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt.buckets import BucketEntry

from gitaudit.analysis.merge_debt.matchers import SameCommitMatcher, MatchConfidence

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


class TestSameCommitMatcher(TestCase):
    def test_branched_version(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(DEV_LOG),
        ))

        matcher = SameCommitMatcher()
        matches = matcher.match(dev_buckets, main_buckets)

        for match in matches:
            self.assertEqual(match.confidence, MatchConfidence.ABSOLUTE)
            self.assertEqual(match.head.sha, match.base.sha)

        self.assertListEqual(
            sorted(list(map(lambda x: x.head.sha, matches))),
            ['a21', 'a6c', 'b8b', 'cf7', 'cfd', 'eae'],
        )
