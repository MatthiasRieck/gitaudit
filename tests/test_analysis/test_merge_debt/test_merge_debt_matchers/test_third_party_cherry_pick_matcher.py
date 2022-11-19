from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt.buckets import BucketEntry

from gitaudit.analysis.merge_debt.matchers import ThirdPartyCherryPickMatcher, MatchConfidence

from .test_case_cherry_picked import CHERRY_PICK_MAIN_LOG, CHERRY_PICK_DEV_LOG


class TestDirectCherryPickMatcher(TestCase):
    def test_third_party_sha(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        ))

        matcher = ThirdPartyCherryPickMatcher()
        matches = matcher.match(dev_buckets, main_buckets)

        for match in matches:
            self.assertEqual(
                match.confidence,
                MatchConfidence.ABSOLUTE,
            )

        matches_map = {x.head.sha: x.base.sha for x in matches}

        self.assertDictEqual(
            matches_map,
            {
                "97b": "f0d",
            },
        )
