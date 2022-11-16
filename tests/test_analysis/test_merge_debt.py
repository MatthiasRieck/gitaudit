from unittest import TestCase

from gitaudit.git.change_log_entry import ChangeLogEntry
from gitaudit.analysis.merge_debt import get_head_base_hier_logs

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
