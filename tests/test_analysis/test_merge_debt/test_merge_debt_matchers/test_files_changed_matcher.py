from unittest import TestCase
from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.branch.hierarchy import linear_log_to_hierarchy_log
from gitaudit.analysis.merge_debt.buckets import BucketEntry

from gitaudit.analysis.merge_debt.matchers import FilesChangedMatcher, MatchConfidence
from .test_case_files_changed_matcher import \
    FILES_CHANGED_MAIN_LOG, FILES_CHANGED_DEV_LOG


class TestFilesChangedMatcher(TestCase):
    def test_with_adddel(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_DEV_LOG),
        ))

        matcher = FilesChangedMatcher()
        matches = matcher.match(dev_buckets, main_buckets)

        for match in matches:
            self.assertEqual(
                match.confidence,
                MatchConfidence.STRONG,
            )

        matches_map = {x.head.sha: x.base.sha for x in matches}

        self.assertDictEqual(
            matches_map,
            {
                "233": "9db",
            },
        )

    def test_without_adddel(self):
        main_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_MAIN_LOG),
        ))

        dev_buckets = BucketEntry.list_from_change_log_list(linear_log_to_hierarchy_log(
            ChangeLogEntry.list_from_objects(FILES_CHANGED_DEV_LOG),
        ))

        matcher = FilesChangedMatcher(with_additions_deletions=False)
        matches = matcher.match(dev_buckets, main_buckets)

        for match in matches:
            self.assertEqual(
                match.confidence,
                MatchConfidence.GOOD,
            )

        matches_map = {x.head.sha: x.base.sha for x in matches}

        self.assertDictEqual(
            matches_map,
            {
                "f65": "1e2",
            },
        )
