from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt.buckets import BucketEntry

from gitaudit.analysis.merge_debt.matchers import DirectCherryPickMatcher, MatchConfidence

from .test_case_cherry_picked import CHERRY_PICK_MAIN_LOG, CHERRY_PICK_DEV_LOG


class TestDirectCherryPickMatcher(TestCase):
    def test_both_ways(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        ))

        matcher = DirectCherryPickMatcher()
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
                "431": "1e2",
                "a6c": "a19",
                "6b6": "f07",
                "79c": "99f",
                "562": "8d0",
                "9fb": "a34",
            },
        )

    def test_head_to_base(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        ))

        matcher = DirectCherryPickMatcher(
            head_to_base=True, base_to_head=False)
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
                # "431": "1e2",
                "a6c": "a19",
                # "6b6": "f07",
                "79c": "99f",
                # "562": "8d0",
                "9fb": "a34",
            },
        )

    def test_base_to_head(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(CHERRY_PICK_DEV_LOG),
        ))

        matcher = DirectCherryPickMatcher(
            head_to_base=False, base_to_head=True)
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
                "431": "1e2",
                # "a6c": "a19",
                "6b6": "f07",
                # "79c": "99f",
                "562": "8d0",
                # "9fb": "a34",
            },
        )
