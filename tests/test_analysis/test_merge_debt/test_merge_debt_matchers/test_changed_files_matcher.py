from unittest import TestCase
from gitaudit.analysis.merge_debt.matchers import numstat_to_sha1, create_numstat_map
from gitaudit.git.change_log_entry import ChangeLogEntry, FileAdditionsDeletions


class TestNumstatToSha1(TestCase):
    def test_no_changes(self):
        entry = ChangeLogEntry.parse_obj({
            "sha": "a",
            "parent_shas": [],
        })
        self.assertEqual(
            numstat_to_sha1(entry),
            'da39a3ee5e6b4b0d3255bfef95601890afd80709',
        )

    def test_with_numstat(self):
        entry = ChangeLogEntry.parse_obj({
            "sha": "a",
            "parent_shas": [],
            "numstat": [
                {
                    "path": "/a/b/c",
                    "additions": 2,
                    "deletions": 3,
                },
                {
                    "path": "/a/c",
                    "additions": 5,
                    "deletions": 6,
                }
            ]
        })
        self.assertEqual(
            numstat_to_sha1(entry, with_additions_deletions=False),
            'adaba0746dbe259e9f2b724d0c3202e26829a411',
        )
        self.assertEqual(
            numstat_to_sha1(entry, with_additions_deletions=True),
            '219f05c9e377ad0ce4837a07520c3b4d54bd7d9f',
        )


class TestCreateNumstatMap(TestCase):
    def test_create_empty(self):
        numstat_map = create_numstat_map([])
        self.assertDictEqual(numstat_map, {})

    def test_entry_with_no_changes(self):
        numstat_map = create_numstat_map([
            ChangeLogEntry(
                sha="a",
            )
        ])
        self.assertDictEqual(numstat_map, {})

    def test_two_normal_entries_w_adddel(self):
        entry_one = ChangeLogEntry(
            sha="1",
            numstat=[
                FileAdditionsDeletions(path="/a/b", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/c", additions=2, deletions=3),
            ]
        )
        entry_two = ChangeLogEntry(
            sha="2",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        numstat_map = create_numstat_map([entry_one, entry_two])

        self.assertDictEqual(numstat_map, {
            '11b520f2c6ca02e45bfca6f22b35fa29ea4994b9': entry_one,
            '71349dffae78dea72e0a4d4049ed8c2e7f3febc7': entry_two,
        })

    def test_two_normal_entries_wo_adddel(self):
        entry_one = ChangeLogEntry(
            sha="1",
            numstat=[
                FileAdditionsDeletions(path="/a/b", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/c", additions=2, deletions=3),
            ]
        )
        entry_two = ChangeLogEntry(
            sha="2",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        numstat_map = create_numstat_map(
            [entry_one, entry_two],
            with_additions_deletions=False,
        )

        self.assertDictEqual(numstat_map, {
            'a98ad3be9c0ea7fcb87243d9a88f491054e92f96': entry_one,
            '6f413a566ee256771cbcfa1c06937a09bcaaab50': entry_two,
        })

    def test_duplicate_numstat(self):
        entry_one = ChangeLogEntry(
            sha="1",
            numstat=[
                FileAdditionsDeletions(path="/a/b", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/c", additions=2, deletions=3),
            ]
        )
        entry_two = ChangeLogEntry(
            sha="2",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        entry_duplicate_two = ChangeLogEntry(
            sha="d",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        numstat_map = create_numstat_map(
            [entry_one, entry_two, entry_duplicate_two],
            with_additions_deletions=False,
        )

        self.assertDictEqual(numstat_map, {
            'a98ad3be9c0ea7fcb87243d9a88f491054e92f96': entry_one,
        })

    def test_two_duplicate_numstat(self):
        entry_one = ChangeLogEntry(
            sha="1",
            numstat=[
                FileAdditionsDeletions(path="/a/b", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/c", additions=2, deletions=3),
            ]
        )
        entry_two = ChangeLogEntry(
            sha="2",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        entry_duplicate_two = ChangeLogEntry(
            sha="d",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        entry_duplicate_two2 = ChangeLogEntry(
            sha="d2",
            numstat=[
                FileAdditionsDeletions(path="/a/d", additions=1, deletions=1),
                FileAdditionsDeletions(path="/a/e", additions=2, deletions=3),
            ]
        )
        numstat_map = create_numstat_map(
            [entry_one, entry_two, entry_duplicate_two, entry_duplicate_two2],
            with_additions_deletions=False,
        )

        self.assertDictEqual(numstat_map, {
            'a98ad3be9c0ea7fcb87243d9a88f491054e92f96': entry_one,
        })
